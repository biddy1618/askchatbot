

# Script to evaluate pretrained RawNet2 model on evaluation datasets.
# RawNet2 is written in PyTorch. We therefore have to implement a PyTorch
# Dataset class to represent our evaluation dataset.

import torch
import sys
import os
from tqdm import tqdm
import yaml  # To read RawNet2 configuration file (copied from ASVspoof)
from metrics import plot_det  # Detection Error Trade-off plot, Equal error rate
import numpy as np   # For array stuff
import mlflow   # For logging metrics
import librosa  # For loading the audio file
from models import models_dict
from model import RawNet
from config import *  # Import configuration and helper functions
from training import TamperingDetectionModel



# Copied from ASVspoof
# Ensures that the returned audio is exactly 4 seconds (or max_len datapoints) long.
# By either truncating it at the beginning if it is longer, or
# by repeating the same audio over and over until it is 4 seconds.
def pad(x, max_len=64600):
    x_len = x.shape[0]
    if x_len >= max_len:
        return x[:max_len]
    # need to pad
    num_repeats = int(max_len / x_len)+1
    padded_x = np.tile(x, (1, num_repeats))[:, :max_len][0]
    return padded_x
class EvalDataset(torch.utils.data.Dataset):
    def __init__(self, filelist_path, base_dir):
        self.filelist_path = filelist_path
        self.base_dir = base_dir
        with open(self.filelist_path, 'r', encoding='utf-8') as txt_file:
            self.files = []
            self.targets = []
            for line in txt_file:
                line = line.strip()
                items = line.split(",", maxsplit=1)
                if len(items) == 2:
                    self.files.append(items[1])
                    self.targets.append(int(items[0]))

    def __len__(self):
        return len(self.files)

    def __getitem__(self, index):
        cut = 64600  # take ~4 sec audio (64600 samples)
        # Read audio file
        audio, samplerate = librosa.load(os.path.join(self.base_dir, self.files[index]), sr=16000)
        # Pad it to ensure it is 4 seconds long
        audio_pad = pad(audio, cut)
        # Make it a torch Tensor
        audio_pad = torch.Tensor(audio_pad)
        # Return audio and target
        return audio_pad, self.targets[index]


if __name__ == "__main__":
    # Start of the program

    artifact_uri = os.getenv("ARTIFACT_URI", None)
    trained_ourselves = False if artifact_uri is None else True

    # Check if GPU is available, otherwise use CPU
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print('Device: {}'.format(device))

    # Define model
    model_name = os.getenv("MODEL_NAME")
    # We first need to read the model configuration file (.yaml)
    with open(os.path.join("conf", model_name + ".yml"), 'r') as f_yaml:
        model_config = yaml.load(f_yaml, Loader=yaml.FullLoader)

    # Load model weights
    # Check if we're using our own models from MLflow, or pretrained source models
    if not trained_ourselves:
        # Then, we create the model architecture
        build_model_function = models_dict[model_name]
        model = build_model_function(model_config["model"])
        model = model.to(device)
        # Load pretrained source model
        model.load_state_dict(
            torch.load(
                os.path.join(os.getenv("WORK_DIR"), model_config["pretrained"]),
                map_location=device
            )
        )
    else:
        artifact_path = os.getenv("ARTIFACT_PATH")
        if artifact_path.endswith(".ckpt"):
            # If we're loading from a PyTorch Lightning checkpoint, try the following:
            print(f"Trying to load Pytorch Lightning model checkpoint from '{artifact_path}'.")
            # Then, we create the model architecture
            # model = RawNet(model_config["model"], device)
            build_model_function = models_dict[model_name]
            model = build_model_function(model_config["model"], device)
            model = model.to(device)
            ptl_model = TamperingDetectionModel(model, config, model_config)
            ptl_model.load_state_dict(
                torch.load(
                    artifact_path,
                    map_location=device
                )['state_dict'],
                strict=False
            )
            model = ptl_model.model
            model = model.to(device)
            # model = torch.jit.script(model)
            # model.save(os.path.join(os.getenv("WORK_DIR"), 'model_scripted.pt'))
        elif artifact_path.endswith(".pt"):
            # TorchScript model (for deployment)
            model = torch.jit.load(artifact_path, map_location=device)
            model = model.to(device)
        elif artifact_path.endswith(".pth"):
            # # If we're loading from a PyTorch Lightning model, try the following:
            # print(f"Trying to load Pytorch Lightning model from '{artifact_path}'.")
            # # Then, we create the model architecture
            # model = RawNet(model_config["model"], device)
            # model = model.to(device)
            # ptl_model = TamperingDetectionModel(model, config, model_config)
            # ptl_model.load_state_dict(
            #     torch.load(
            #         artifact_path,
            #         map_location=device
            #     ),
            #     strict=False
            # )
            # model = ptl_model.model
            model = torch.load(artifact_path, map_location=device)
            model = model.to(device)
    # sys.exit(0)
    # Create evaluation dataset
    eval_dataset = EvalDataset(
        os.getenv("TEST_FILELIST"),
        os.getenv("DATA_DIR")
    )
    # Create data loader from dataset (which creates batches etc.)
    data_loader = torch.utils.data.DataLoader(
        eval_dataset,
        batch_size=int(os.getenv("BATCH_SIZE", 1)),
        shuffle=False,
        drop_last=False,
        num_workers=int(os.getenv("NUM_WORKERS", 1))
    )
    # Put model in evaluation mode
    model.eval()
    # Go through all batches
    y_score = []
    y_pred = []
    y_true = []
    num_total = 0
    num_correct = 0
    for audios, targets in tqdm(data_loader):
        # Copy audios to device (GPU or CPU memory)
        audios = audios.to(device)
        # Update counts for calculating accuracy
        num_total += audios.size(0)
        # In our own training data, the targets are 0==human and 1==tampered;
        # however, the pretrained models from ASVspoof have the targets flipped.
        if trained_ourselves:
            # Run model on audios
            _, scores = model(audios)
            _, pred = scores.max(dim=1)
            # Get scores from the output as numpy array
            scores = (scores[:, 1]).data.cpu().numpy().ravel()
        else:
            # Run model on audios
            _, scores = model(audios)
            # Here, we use min instead of max, because our targets are flipped
            # compared to what the pretrained model has been trained with
            _, pred = scores.min(dim=1)
            # Get scores from the output as numpy array
            #   Note that we multiply scores by -1.0, because in ASVspoof2019,
            #   the labels 0,1 are swapped
            scores = (scores[:, 1]).data.cpu().numpy().ravel() * -1.0
        num_correct += (pred == targets.to(device)).sum(dim=0).item()
        # Add scores for batch to all scores
        y_score.extend(scores.tolist())
        # Add true values for batch to all true values
        y_true.extend(targets.numpy().ravel().tolist())
        y_pred.extend(pred.cpu().numpy().ravel().tolist())

    # Compute accuracy
    accuracy = (num_correct / num_total)
    # Convert to numpy arrays
    y_score = np.asarray(y_score)
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_true)

    path = os.path.join(os.getenv("WORK_DIR"), 'eval_' + os.getenv("EVAL_NAME"))
    os.makedirs(path, exist_ok=True)
    # Save y_true and y_score to disk
    with open(os.path.join(path, 'y_true.npy'), 'wb') as f:
        np.save(f, y_true)
    with open(os.path.join(path, 'y_score.npy'), 'wb') as f:
        np.save(f, y_score)
    with open(os.path.join(path, 'y_pred.npy'), 'wb') as f:
        np.save(f, y_pred)

    # Calculate metrics
    eer = plot_det(os.path.join(path, 'detplot.png'), y_true, y_score)

    # Set MLflow experiment name (MLFLOW_EXPERIMENT_NAME is set in the workflow or docker-compose)
    mlflow.set_experiment(os.getenv('MLFLOW_EXPERIMENT_NAME'))
    # Start an MLflow run
    with mlflow.start_run() as run:
        # Log evaluation results to MLflow
        mlflow.log_metric("eer", eer)
        mlflow.log_metric("acc", accuracy)
        mlflow.log_artifacts(path, os.getenv('EVAL_NAME'))
        mlflow.log_param("eval", os.getenv('EVAL_NAME'))
        mlflow.log_param("model", os.getenv('MODEL_NAME'))
        # If env variable ARTIFACT_URI is set, log it as param "source_model_run"
        if artifact_uri is not None:
            mlflow.log_param("source_model_run", artifact_uri)