import aws_cdk as cdk
from aws_cdk import Stack
from constructs import Construct
from aws_cdk import aws_kinesisfirehose as _kinesis_fh
from aws_cdk import aws_iam as _iam
from aws_cdk import aws_logs as _logs
from aws_cdk import aws_s3 as _s3
from stacks.miztiik_global_args import GlobalArgs
from aws_cdk import aws_apigateway as _apigw


class GlobalArgs:
    """
    Helper to define global statics
    """

    OWNER = "MystiqueAutomation"
    ENVIRONMENT = "production"
    REPO_NAME = "apigw-proxy-for-firehose"
    SOURCE_INFO = f"https://github.com/miztiik/{REPO_NAME}"
    VERSION = "2022_06_03"
    MIZTIIK_SUPPORT_EMAIL = ["mystique@example.com", ]


class ApiGwProxyForFirehoseStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stack_log_level: str,
        back_end_api_name: str,
        fh_stream,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        # Create the API GW service role with permissions to call SQS
        rest_api_role = _iam.Role(
            self,
            "RestAPIRole",
            assumed_by=_iam.ServicePrincipal("apigateway.amazonaws.com"),
            # managed_policies=[ _iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSQSFullAccess")]
        )

        # Add permissions to API GW Execution role to Kinesis Fireshose
        roleStmt1 = _iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            resources=[f"{fh_stream.attr_arn}"],
            actions=[
                "firehose:PutRecord",
                "firehose:PutRecords"
            ]
        )
        roleStmt1.sid = "AllowApiGwToWriteToKinesisFirehose"
        rest_api_role.add_to_policy(roleStmt1)

        roleStmt2 = _iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            resources=["*"],
            actions=[
                "firehose:ListDeliveryStreams"
            ]
        )
        roleStmt2.sid = "AllowApiGwToListKinesisFirehoseStreams"
        rest_api_role.add_to_policy(roleStmt2)

        # Add API GW stage options
        proxy_for_fh_stage_options = _apigw.StageOptions(
            stage_name="prod",
            caching_enabled=False,
            throttling_rate_limit=10,
            throttling_burst_limit=100,
            # Log full requests/responses data
            data_trace_enabled=True,
            # Enable Detailed CloudWatch Metrics
            metrics_enabled=True,
            logging_level=_apigw.MethodLoggingLevel.INFO
        )

        # Create API Integration Response object: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_apigateway/IntegrationResponse.html
        proxy_for_fh_api_integration_response = _apigw.IntegrationResponse(
            status_code="200",
            response_templates={"application/json": ""},

        )

        # Create API Integration Options object: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_apigateway/IntegrationOptions.html
        proxy_for_fh_api_integration_options = _apigw.IntegrationOptions(
            credentials_role=rest_api_role,
            integration_responses=[proxy_for_fh_api_integration_response],
            request_templates={
                "application/json": "#set($inputRoot = $input.path('$'))\n"
                                    "{\"DeliveryStreamName\": \"$inputRoot.DeliveryStreamName\",\n \"Record\": {\"Data\": \"$inputRoot.Data\"}}"
            },
            passthrough_behavior=_apigw.PassthroughBehavior.NEVER,
            request_parameters={
                "integration.request.header.Content-Type": "'application/x-amz-json-1.1'"
            }
        )

        # Create API Gateway
        proxy_for_fh_api = _apigw.RestApi(
            self,
            "backEnd01Api",
            rest_api_name=f"{back_end_api_name}",
            deploy_options=proxy_for_fh_stage_options,
            endpoint_types=[
                _apigw.EndpointType.REGIONAL
            ],
            description=f"{GlobalArgs.OWNER}: API Best Practices. This stack deploys an API with AWS Integration for Firehose"
        )

        proxy_for_fh_api_res = proxy_for_fh_api.root.add_resource("fh-proxy")
        list_streams = proxy_for_fh_api_res.add_resource("list-streams")

        list_streams_method_get = list_streams.add_method(
            http_method="GET",
            request_parameters={
                "method.request.header.InvocationType": True,
                "method.request.path.skon": True
            },
            integration=_apigw.AwsIntegration(
                service="firehose",
                integration_http_method="POST",
                action="ListDeliveryStreams",
                region="us-east-2",
                options=proxy_for_fh_api_integration_options
            ),
            method_responses=[
                _apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                )
            ]
        )

        evnt_ingest = proxy_for_fh_api_res.add_resource("event-ingest")

        evnt_ingest_method_post = evnt_ingest.add_method(
            http_method="POST",
            request_parameters={
                "method.request.header.InvocationType": True,
                "method.request.path.skon": True
            },
            integration=_apigw.AwsIntegration(
                service="firehose",
                integration_http_method="POST",
                action="PutRecord",
                region="us-east-2",
                options=proxy_for_fh_api_integration_options
            ),
            method_responses=[
                _apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                )
            ]
        )

        ###########################################
        ################# OUTPUTS #################
        ###########################################
        output_0 = cdk.CfnOutput(
            self,
            "AutomationFrom",
            value=f"{GlobalArgs.SOURCE_INFO}",
            description="To know more about this automation stack, check out our github page."
        )
