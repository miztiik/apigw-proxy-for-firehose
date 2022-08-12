#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.back_end.s3_stack.s3_stack import S3Stack
from stacks.back_end.firehose_stack.firehose_stack import FirehoseStack
from stacks.back_end.apigw_proxy_for_firehose_stack.apigw_proxy_for_firehose_stack import ApiGwProxyForFirehoseStack


app = cdk.App()

# S3 Bucket to hold our sales events
sales_events_bkt_stack = S3Stack(
    app,
    # f"{app.node.try_get_context('project')}-sales-events-bkt-stack",
    f"sales-events-bkt-stack",
    stack_log_level="INFO",
    description="Miztiik Automation: S3 Bucket to hold our sales events"
)


# Kinesis Firehose Stack
firehose_stack = FirehoseStack(
    app,
    # f"{app.node.try_get_context('project')}-job-stack",
    f"firehose-stack",
    stack_log_level="INFO",
    sales_evnt_bkt=sales_events_bkt_stack.data_bkt,
    description="Miztiik Automation: Kinesis Firehose Stack"
)

ApiGwProxyForFirehoseStack = ApiGwProxyForFirehoseStack(
    app,
    # f"{app.node.try_get_context('project')}-job-stack",
    f"apigw-proxy-for-firehose-stack",
    stack_log_level="INFO",
    back_end_api_name="firehose-proxy-api",
    fh_stream=firehose_stack.get_fh_stream,
    description="Miztiik Automation: Kinesis Firehose Stack"
)


# Stack Level Tagging
_tags_lst = app.node.try_get_context("tags")

if _tags_lst:
    for _t in _tags_lst:
        for k, v in _t.items():
            cdk.Tags.of(app).add(
                k, v, apply_to_launched_instances=True, priority=300)

app.synth()
