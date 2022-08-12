import aws_cdk as cdk
from aws_cdk import Stack
from constructs import Construct
from aws_cdk import aws_kinesisfirehose as _kinesis_fh
from aws_cdk import aws_iam as _iam
from stacks.miztiik_global_args import GlobalArgs


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


class FirehoseStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stack_log_level: str,
        sales_evnt_bkt,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        self.firehose_delivery_stream_name = f"sales_events_ingestor"

        fh_delivery_role = _iam.Role(
            self,
            "fhDeliveryRole",
            # role_name="FirehoseDeliveryRole",
            assumed_by=_iam.ServicePrincipal("firehose.amazonaws.com")
        )

        # Add permissions to allow Kinesis Fireshose to Write to S3
        roleStmt1 = _iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            resources=[f"{sales_evnt_bkt.bucket_arn}",
                       f"{sales_evnt_bkt.bucket_arn}/*"
                       ],
            actions=[
                "s3:AbortMultipartUpload",
                "s3:GetBucketLocation",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:ListBucketMultipartUploads",
                "s3:PutObject"
            ]
        )
        # roleStmt1.add_resources(
        #     fh_data_store.arn_for_objects("*")
        # )
        roleStmt1.sid = "AllowKinesisToWriteToS3"
        fh_delivery_role.add_to_policy(roleStmt1)

        # Add permissions to Kinesis Fireshose to Write to CloudWatch Logs
        roleStmt2 = _iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            resources=[
                f"arn:aws:logs:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:log-group:/aws/kinesisfirehose/{self.firehose_delivery_stream_name}:log-stream:*"
            ],
            actions=[
                "logs:PutLogEvents"
            ]
        )
        roleStmt2.sid = "AllowKinesisToWriteToCloudWatch"
        fh_delivery_role.add_to_policy(roleStmt2)

        self.fh_to_s3 = _kinesis_fh.CfnDeliveryStream(
            self,
            "fhDeliveryStream",
            delivery_stream_name=f"{self.firehose_delivery_stream_name}",
            delivery_stream_type=f"DirectPut",
            # kinesis_stream_source_configuration=_kinesis_fh.CfnDeliveryStream.KinesisStreamSourceConfigurationProperty(
            #     kinesis_stream_arn=f"{src_stream.stream_arn}",
            #     role_arn=f"{fh_delivery_role.role_arn}"),
            extended_s3_destination_configuration=_kinesis_fh.CfnDeliveryStream.ExtendedS3DestinationConfigurationProperty(
                bucket_arn=sales_evnt_bkt.bucket_arn,
                buffering_hints=_kinesis_fh.CfnDeliveryStream.BufferingHintsProperty(
                    interval_in_seconds=60,
                    size_in_m_bs=1
                ),
                compression_format="UNCOMPRESSED",
                prefix=f"sales-events/",
                # prefix="phi-data/date=!{timestamp:yyyy}-!{timestamp:MM}-!{timestamp:dd}/",
                role_arn=fh_delivery_role.role_arn,
                # processing_configuration=_kinesis_fh.CfnDeliveryStream.ProcessingConfigurationProperty(
                #     enabled=True,
                #     processors=[
                #         _kinesis_fh.CfnDeliveryStream.ProcessorProperty(
                #             parameters=[
                #                 _kinesis_fh.CfnDeliveryStream.ProcessorParameterProperty(
                #                     parameter_name="LambdaArn",
                #                     parameter_value=fh_transformer_fn.function_arn,
                #                 )
                #             ],
                #             type="Lambda",
                #         )
                #     ]
                # ),
            ),
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

        output_1 = cdk.CfnOutput(
            self,
            "FirehoseArn",
            value=f"https://console.aws.amazon.com/firehose/home?region={cdk.Aws.REGION}#/details/{self.fh_to_s3.delivery_stream_name}",
            description="Kinesis Firehose to persist data events to S3."
        )
        output_2 = cdk.CfnOutput(
            self,
            "FirehoseDeliveryStreamName",
            value=f"{self.firehose_delivery_stream_name}",
            description="Kinesis Firehose Delivery Stream Name."
        )

    # properties to share with other stacks
    @property
    def get_fh_stream(self):
        return self.fh_to_s3
