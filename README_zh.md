# 图像可视化与选择工具

## 安装依赖

    pip install -r requirement.txt

## 懒人模式

如果你懒, 请忽略下面的配置参数和启动服务, 直接运行并用浏览器访问

    bash run_example.sh

## 配置参数

    vim config/config.json
    # 参数说明:
    # database, 数据库路径, 一些相关数据将会存储到这个数据库里面, 例如可以设置为"./example.db"
    # default_dir, 默认显示路径, 例如"/home"
    # permitted_dirs, 允许访问的路径列表, 例如["/home", "/mnt"]

## 启动服务

    # 初始化数据库
    db=./example.db
    schema=schema.sql
    if [ ! -d ${db} ];then
        sqlite3 ${db} < ${schema}
    fi
    
    # 设置启动参数
    host=0.0.0.0
    port=8000
    cfg=config/config.json
    threaded=1
    debug=0
    
    # 启动服务
    python viewer.py \
        --host ${host} \
        --port ${port} \
        --cfg ${cfg} \
        --threaded ${threaded} \
        --debug ${debug}
    
## 通过浏览器访问

假设服务器的ip是10.10.10.31, 使用port 8000, 则通过本地浏览器访问

    http://10.10.10.31:8000
