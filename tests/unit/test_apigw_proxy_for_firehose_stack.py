import aws_cdk as core
import aws_cdk.assertions as assertions

from apigw_proxy_for_firehose.apigw_proxy_for_firehose_stack import ApigwProxyForFirehoseStack

# example tests. To run these tests, uncomment this file along with the example
# resource in apigw_proxy_for_firehose/apigw_proxy_for_firehose_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ApigwProxyForFirehoseStack(app, "apigw-proxy-for-firehose")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
