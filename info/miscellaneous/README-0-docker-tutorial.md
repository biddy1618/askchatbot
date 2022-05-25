# Dockerfile reference


## `FROM` instruction

Used for base image defintion
- `ARG` is the only instruction that may precede `FROM` and variable may be declared for `ARG` to be used in `FROM`
- The `AS name` can be used in subsequent `FROM` and `COPY` instructions to refer to the image in this stage


```dockerfile
# syntax=docker/dockerfile:1                        # syntax directive defines the location of the Dockerfile syntax that is used to build the Dockerfile
# escape=\ (backslash)                              # set the escape characted in Dockerfile
# About                                             # description of the Dockerfile

ARG VERSION=<version>
FROM <image>:$VERSION AS <name>
```

### Command exections commands - exec and shell methods
2 forms: exec - `COMMAND ["bash", "-c", "echo $HOME"]` and shell - `COMMAND bash -c "echo $HOME"`
- Main difference is that exec form doesn't invoke a command shell.
- __NOTE__: whenever using `bash (sh) -c arg` or `['bash' ('sh'), '-c', 'arg']` make sure to wrapt the args in single string, i.e. `bash -c` and `sh -c` expect a string as an argument.
- More about the difference bewtween shell and exec form [here](https://stackoverflow.com/questions/42805750/differences-between-dockerfile-instructions-in-shell-and-exec-form).


## `RUN` instruction

`RUN` instruction will exectute any commands in a new layer on top of the current image and commit the results.

```dockerfile
RUN <command>                                       # shell form
RUN ["executable", "param1", "param2"]              # exec form
```

## `CMD` instruction

- `CMD` instruction - there can be only one `CMD` instruction. Main purpose is to provide defaults parameters to `ENTRYPOINT`.
- If `ENTRYPOINT` is not defined, the default value for `ENTRYPOINT` is `sh -c`.
```dockerfile
CMD ["param1", "param2"]                            # exec form
CMD command param1 param2                           # shell form
```

## `EXPOSE` instruction

Instruction informs Dokcer gthat hte container listens on the specified netweork on the specified ports at runtime.
The default is TCP if the protocol is not specified.

```dockerfile
EXPOSE <port> [<port>/<protocol>]
# EXPOSE 80/tcp
# EXPOSE 80/udp
```

## `ENV` instruction

Sets the environment variable `<key>` to the value `<value>`.

```dockerfile
ENV <key>=<value> ...
# ENV MY_NAME="John Doe"
# ENV MY_DOG=Rex\ The\ Dog
# ENV MY_CAT=fluffy
```
If an enviroment variable is only needed during build, and not in the final image, consider setting a value for a single command instead:
```dockerfile
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y ...
# ARG DEBIAN_FRONTED=noninteractive
# RUN apt-get update && apt=get install -y ...
```

## `COPY` instruction

The `COPY` instruction copies new files or directories from `<src>` and adds them to the filesystem of the container at the path `<dest>`.

```dockerfile
COPY [--chown=<user>:<group>] <src>... <dest>
# COPY [--chown=<user>:<group>] ["<src>",... "<dest>"]
```

## `ADD` instruction

The `ADD` instuction is like `COPY` but can do a little more:
- __remote file URLs__ 
- and copy and unpack recognized compressed file (identity, gzip, bzip2, or xz).

I.e., `ADD` is same as 'COPY', but with the tar and remote URL handling.

Best practices suggest that using `COPY` where the magic of `ADD` is not required.

```dockerfile
ADD [--chown=<user>:<group>] <src>... <dest>
# ADD [--chown=<user>:<group>] ["<src>",... "<dest>"]
```

## `ENTRYPOINT` instruction

An `ENTRYPOINT` allows you to configure a container that will run as an executable.

```dockerfile
ENTRYPOINT ["executable", "param1", "param2"]       # preferred form
# ENTRYPOINT command param1 param2
```

The table below shows what command is executed for different `ENTRYPOINT` / `CMD` combinations:
|                            | No ENTRYPOINT              | ENTRYPOINT exec_entry p1_entry | ENTRYPOINT [“exec_entry”, “p1_entry”]          |
|----------------------------|----------------------------|--------------------------------|------------------------------------------------|
| No CMD                     | error, not allowed         | /bin/sh -c exec_entry p1_entry | exec_entry p1_entry                            |
| CMD [“exec_cmd”, “p1_cmd”] | exec_cmd p1_cmd            | /bin/sh -c exec_entry p1_entry | exec_entry p1_entry exec_cmd p1_cmd            |
| CMD [“p1_cmd”, “p2_cmd”]   | p1_cmd p2_cmd              | /bin/sh -c exec_entry p1_entry | exec_entry p1_entry p1_cmd p2_cmd              |
| CMD exec_cmd p1_cmd        | /bin/sh -c exec_cmd p1_cmd | /bin/sh -c exec_entry p1_entry | exec_entry p1_entry /bin/sh -c exec_cmd p1_cmd |


## `VOLUME` instruction

The `VOLUME` instruction creates a mount point with the specified name and marks it as holding externally mounted volumes from native host or other containers. 

As per this [post](https://stackoverflow.com/questions/52570093/what-is-the-practical-purpose-of-volume-in-dockerfile), "tl;dr: VOLUME was designed for a world before Docker 1.9. Best to just leave it out."

In short, specifiying `VOLUME` in docker may help in performance issues (like specifying data volume in postgres dockerfile) by keeping the data out of the layered filesystem.
```dockerfile
VOLUME ["/data"]
```
For mounting purposes, use the runtime command `run` with `-v` parameter.

## `USER` instruction

The `USER` instruction sets the user name (or UID) and optionally the user group (or GID) to use when running the image and for any `RUN`, `CMD` and `ENTRYPOINT` instructions that follow it in the Dockerfile.

```dockerfile
USER <user>[:<group>]
```
Uf yser doesn't have a primary group, it will be run with the `root` group.


## `WORKDIR` instruction

The `WORKDIR` instruction sets the working directory for any `RUN`, `CMD`, `ENTRYPOINT`, `COPY` and `ADD` instructions that follow it in the Dockerfile. If the `WORKDIR` doesn’t exist, it will be created even if it’s not used in any subsequent Dockerfile instruction.

```dockerfile
WORKDIR /path/to/workdir
# ENV DIRPATH=/path
# ENV DIRNAME=/dirname
# WORKDIR $DIRPATH/$DIRNAME
# RUN pwd                                           # The output of the final pwd command in this Dockerfile would be /path/dirname
```

---

For further reading, visit [Docker best practices page](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/).