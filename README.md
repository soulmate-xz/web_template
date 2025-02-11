# fastapi restful 服务后台

## 开发规范
- 代码提交前先运行代码检测
  ```shell
    pre-commit run --all-files
  ```

- 不允许大量使用忽略类型检查的注释, 如必须使用需注明原因
  ```shell
      # type: ignore 由于xxx原因忽略此处检测
  ```

- 接口编写完成后需编写测试用例, 测试覆盖率需达到95%以上
- 数据库更改需生成更改记录(alembic)


## 测试
```shell
pytest --cov
```

## 运行
* web
  - 正式环境
    ```shell
      gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 backend.asgi:app
    ```
  - 测试环境
    ```shell
      uvicorn backend.asgi:app --host 0.0.0.0 --port 8080
    ```
