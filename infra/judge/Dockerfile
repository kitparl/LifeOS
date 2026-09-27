# go-judge (the sandbox Hydro's judge daemon uses) + the DSA launch toolchains:
# g++ (C++17), OpenJDK 17, Python 3, Node.js 20. All tags pinned (SECURITY-10).
FROM criyle/go-judge:v1.12.3 AS gojudge
FROM node:20.19.6-bookworm-slim AS node

FROM debian:bookworm-20260918-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends g++ openjdk-17-jdk-headless python3 \
 && rm -rf /var/lib/apt/lists/*
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=gojudge /opt/go-judge /opt/go-judge
COPY mount.yaml entrypoint.sh /opt/
WORKDIR /opt
EXPOSE 5050
ENTRYPOINT ["/bin/sh", "/opt/entrypoint.sh"]
