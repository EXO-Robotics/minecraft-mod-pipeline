# syntax=docker/dockerfile:1.7
FROM --platform=linux/amd64 python@sha256:72d3d75f2639ab82b34b29390ad3d6e0827c775befee94edda8e9976818f488d AS python_runtime
FROM --platform=linux/amd64 itzg/minecraft-bedrock-server@sha256:2944da377164a7cc8bcf29c1d2fd50d0d863c6476e23923384ec55dc7dc4627a

USER root
COPY --from=python_runtime /usr/local /usr/local
COPY --from=bds_seed --chown=65532:65532 / /opt/crazycraft/bds/stable-1.26.33.2/
COPY --from=base_world --chown=65532:65532 /resonance-sling-INTERNAL-TEST.mcworld /opt/crazycraft/fixtures/base-world.mcworld
COPY --chown=65532:65532 --chmod=0555 qualify_exact_package.py /opt/crazycraft/bin/qualify-exact-package

USER 65532:65532
ENTRYPOINT []
CMD ["/opt/crazycraft/bin/qualify-exact-package", "--help"]
