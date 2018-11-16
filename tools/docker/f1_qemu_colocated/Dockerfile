FROM integration_base_x86_64:latest

ARG path_to_host_os

# Add startup script
COPY startup.sh startup.sh

ENTRYPOINT ["./startup.sh"]
