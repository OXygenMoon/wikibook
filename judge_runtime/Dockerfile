FROM python:3.12-alpine

RUN apk add --no-cache gcc g++ musl-dev

WORKDIR /runner
COPY judge_runtime/run_submission.py /runner/run_submission.py

CMD ["python", "/runner/run_submission.py"]
