Run one durable Crazy Craft T1 dispatcher cycle:

`python3 /Users/blakegrove/Desktop/bedrock-server/program/crazycraft-persistent-orchestrator-v1/stabilization-v1/pack-factory-v1/services/t1_dispatcher/t1_dispatcher.py --run-once`

Then read `--pending-resumes`. For each request still in `PENDING_SEND`, verify
that no active writer owns the listed repository and send the exact stored
prompt to the listed existing Codex task ID. On successful send, acknowledge
the request with:

`python3 /Users/blakegrove/Desktop/bedrock-server/program/crazycraft-persistent-orchestrator-v1/stabilization-v1/pack-factory-v1/services/t1_dispatcher/t1_dispatcher.py --ack-resume REQUEST_ID --ack-status SENT`

Do not create replacement microtask owners. Do not edit pack product,
candidate bytes, shared-runtime authority, tester state, T10 results, or
integration product. Do not wake a worker without a pending request. Continue
one cycle per heartbeat and report only failures requiring attention.
