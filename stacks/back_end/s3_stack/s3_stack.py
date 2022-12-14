import aws_cdk as cdk
from aws_cdk import Stack
from constructs import Construct
from aws_cdk import aws_s3 as _s3
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


class S3Stack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stack_log_level: str,
        custom_bkt_name: str = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.data_bkt = _s3.Bucket(
            self,
            "dataBucket",
            versioned=False,
            # auto_delete_objects=True,
            # removal_policy=cdk.RemovalPolicy.DESTROY,
            # bucket_name="new-app-bucket-example",
        )

        _s3.Bucket(

        )

        ##################################################
        ########         ACCESS POINTS         ###########
        ##################################################

        # Lets set custom bucket name if it is set
        if custom_bkt_name:
            cfn_data_bkt = self.data_bkt.node.default_child
            cfn_data_bkt.add_override("Properties.BucketName", custom_bkt_name)

        # Delegate Privilege management to Access Point in bucket policy
        # https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-points-policies.html#access-points-delegating-control

        self.data_bkt.add_to_resource_policy(
            _iam.PolicyStatement(
                actions=["*"],
                principals=[_iam.AnyPrincipal()],
                resources=[
                    f"{self.data_bkt.bucket_arn}",
                    f"{self.data_bkt.arn_for_objects('*')}"
                ],
                conditions={
                    "StringEquals":
                    {
                        "s3:DataAccessPointAccount": f"{cdk.Aws.ACCOUNT_ID}"
                    }
                }
            )
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
            "SalesEventsBucket",
            value=f"{self.data_bkt.bucket_name}",
            description=f"The datasource bucket name"
        )
        output_2 = cdk.CfnOutput(
            self,
            "dataSourceBucketUrl",
            value=f"https://console.aws.amazon.com/s3/buckets/{self.data_bkt.bucket_name}",
            description=f"Sales events bucket console url"
        )
