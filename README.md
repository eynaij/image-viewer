# image-viewer

`image-viewer` is an awesome tool to check and share data remotely.


# Install

```
python setup.py install
pip install -r requirements.txt
```
Take a check if it installed successfully.

```
image-viewer --version
```

# Configure

```
image-viewer-cfg
```
It will generate a default yaml -- `~/.image-viewer/image-viewer.yaml`

You need to edit `port` , `permiitted_dirs` and `default_dir`.

If you don't have access to the `port`, you have to refer to the administrator.

`permiitted_dirs` is where you allow image-viewer to access.

`default_dir` should be one of `permiitted_dirs`.

# Run

```
image-viewer
```

If no error occurs, open chrome and go to your server address, such as my address `10.16.32.115:8888/`

You might find something like this.

![](./docs/snapshot.png)

Go to the directory containing images -> Clik '创建任务'

Enjoy to use it.

# ChangeLog

- v1.0.0: created by jianye.he in 2020.12.4
