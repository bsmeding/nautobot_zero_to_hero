# Due to incompatibility between protobuf version for cloudvision and napalm-srl
# we need to reinstall the protobuf and napalm-srl packages

docker exec -u 0 -it nzth-nautobot pip install "protobuf==3.20.3" napalm-srl
docker exec -u 0 -it nzth-nautobot_celery_worker_1 pip install "protobuf==3.20.3" napalm-srl
docker-compose restart nautobot celery-worker-1