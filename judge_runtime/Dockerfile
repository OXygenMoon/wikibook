FROM python:3.12-alpine

RUN apk add --no-cache gcc g++ musl-dev

WORKDIR /runner
COPY judge_runtime/run_submission.py /runner/run_submission.py
COPY judge_runtime/python_sandbox.py /runner/python_sandbox.py
COPY judge_security.py /runner/judge_security.py

CMD ["python", "/runner/run_submission.py"]
