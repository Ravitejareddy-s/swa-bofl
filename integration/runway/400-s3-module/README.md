# SWA Cloud Common Platform S3 Module

The S3 module can be used to create a SWA approved AWS S3 bucket. The module provides parameters for lifecycle management, access logging, encryption, versioning configuration. It also requires parameter to indicates whether Logging should be configured or not.

## Configuration Parameters

1. name (*Required*) - All buckets are named using `{department}-{aws_region}-{namespace}-{name}` format. This parameters will be used as the last attribute in the bucket name.

1. enableServerAccessLogging (*Required*) - Indicates whether Logging should be configured or not.

1. enableRequestMetrics (*Optional*) - If *true*, request metrics will be enabled for entire bucket. NOTE: This will be billed as CloudWatch metrics.

1. versioning (*Required*) - Used for [VersioningConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-versioningconfig.html)

1. crrDestinationBucket (*Optional*) - The name of the bucket that will act as the destination for cross region replication.  `crossRegion` must also be specified for this to be used.  If not provided, replication will try to use a bucket name that matches the one you're creating but in the destination region.  **NOTE**: this bucket must already exist in the destination region.

1. crrPrefixFilter (*Optional*) - The prefix that will be added to the cross region replication rule to apply replication to a subset of objects.  If not provided, replication will be applied to all objects in the bucket.  `crossRegion` must also be specified for this to be used.

1. crrDeleteMarkerReplication (*Optional*) - Boolean field that controls if [Delete Marker Replication](https://docs.aws.amazon.com/AmazonS3/latest/userguide/delete-marker-replication.html) is enabled. If *True*, deletion of objects will be replicated to the `crrDestinationBucket`. If not provided or *False*, delete marker replication will be disabled.  `crossRegion` must also be specified for this to be used.

1. crossRegion (*Optional*) - The region name of the cross region to replicate this bucket. If defined, cross region replication will be configured. In order to do this a bucket must be created in the specified cross region with replication time control enabled. (<https://docs.aws.amazon.com/AmazonS3/latest/dev/replication.html>)

1. disable_bidirectional_crr (*Optional*) - Boolean field to control whether the cross region replication is created for the source as well as destination buckets. `crossRegion` must be specified for this to be used.

1. replica_modifications (*Optional*) - Boolean field to control object metadata replication such as tags, ACLs, and Object Lock settings between replicas and source objects. `crossRegion` must be specified for this to be used. (<https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication-for-metadata-changes.html>)

1. bucketKeyEnabled (*Optional*) - Boolean field to specify whether S3 should use an S3 Bucket Key with server-side encryption using KMS (SSE-KMS) for new objects in the bucket. `False` by default.

1. lifecycleRules (*Optional*) - If defined, specifies the list of lifecycle rules for objects in s3.

   a. id (*Required*) - Unique identifier for the lifecycle rule . Used for *Id* in [LifecycleConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-lifecycleconfig-rule.html#cfn-s3-bucket-lifecycleconfig-rule-id)

   b. status (*Optional*) - If Enabled, rule is applied. If Disabled, rule is not applied. Used for *Status* in [LifecycleConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-lifecycleconfig-rule.html#cfn-s3-bucket-lifecycleconfig-rule-status)

   c. expirationInDays (*Optional*) - Used for *ExpirationInDays* in [LifecycleConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-lifecycleconfig-rule.html#cfn-s3-bucket-lifecycleconfig-rule-expirationindays).

   d. nonCurrentVersionExpirationInDays (*Optional*) - Used for *NoncurrentVersionExpirationInDays* in [LifecycleConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-lifecycleconfig-rule.html#cfn-s3-bucket-lifecycleconfig-rule-noncurrentversionexpirationindays)

   e. transitions (*Optional*) - Used for *Transitions* in [LifecycleConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-lifecycleconfig-rule.html#cfn-s3-bucket-lifecycleconfig-rule-transitions)

   1. storage (*Required*) - Used for *StorageClass* in [LifecycleConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-lifecycleconfig-rule-transition.html#cfn-s3-bucket-lifecycleconfig-rule-transition-storageclass)

   1. days (*Required*) - Used for *TransitionInDays* in [LifecycleConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-lifecycleconfig-rule-transition.html#cfn-s3-bucket-lifecycleconfig-rule-transition-transitionindays)

   f. expiredObjectDeleteMarker (*Optional*) - Used for *ExpiredObjectDeleteMarker* in [LifecycleConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-lifecycleconfig-rule.html#cfn-s3-bucket-rule-expiredobjectdeletemarker)

   g. prefix (*Optional*) - Used to set the prefix to filter s3 objects for expiration rules.

1. Access Points (*Optional*) Amazon S3 Access Points with either an internet or VPC origin. Only accessible by accounts within the SWA Organization.

   - name (*Required*) - The name of this access point.
   - vpcId (*Optional*) - The Virtual Private Cloud (VPC) ID for this access point. If provided, the access point will not allow access from the internet.
   - bucketPrefix (*Required*) - The prefix of the bucket associated with this access point.
   - writeAccess (*Optional*) - Enable write access on the access point. Set to `true` to enable write access. Default is `false`.
   - role or roles (*Required*) - The IAM role ARN (using `role`) or multiple ARNs (using `roles`).  One or the other *must* be provided for each access point.
     - If `role` is specified, it should be a single ARN:

       ```yaml
         role: arn:aws:iam::437298529078:role/SomeRole-12345
       ```

     - If `roles` is specified, it should be an array for multiple ARNs:

       ```yaml
         roles:
           - arn:aws:iam::437298529078:role/SomeRole-12345
           - arn:aws:iam::437298529078:role/AnotherRole-54321
       ```

1. Alarms (*Optional*) Optional Alarms that you can configure to generate Dash incidents.

   - AssignmentGroup (*Required*) - The assignment group to be used when assigning incidents in DASH. This is required if creating alarms.</br>
     **NOTE** The use of the `serviceConsoleGroup` variable in the environment variables files has been deprecated. Currently, if *AssignmentGroup* has not been set in the Alarms configuration, this module will attempt to use the `serviceConsoleGroup` to assign the DASH incident. This functionality will be removed in the future.

   - Application (*Optional*) - The application to be set in the Configuration Item field. If not provided, only the AssignmentGroup will be used to create the DASH incident.

   - 4xxErrors (\*Optional) - The sum of 4xx errors triggered in a 1 minute period. **NOTE** `enableRequestMetrics` must be set to `true` to create this alarm.

     - EvaluationPeriods (*Optional*) - The number of periods over which data is compared to the specified threshold. Defaults to 1.
     - High (*Optional*) - Threshold for creating a High Dash Event
     - Medium (*Optional*) - Threshold for creating a Medium Dash Event
     - Low (*Optional*) - Threshold for creating a Low Dash Event

   - 5xxErrors (\*Optional) - The sum of 5xx errors triggered in a 1 minute period. **NOTE** `enableRequestMetrics` must be set to `true` to create this alarm.

     - EvaluationPeriods (*Optional*) - The number of periods over which data is compared to the specified threshold. Defaults to 1.
     - High (*Optional*) - Threshold for creating a High Dash Event
     - Medium (*Optional*) - Threshold for creating a Medium Dash Event
     - Low (*Optional*) - Threshold for creating a Low Dash Event1.

   - DeleteRequests (\*Optional) - The sum of delete requests received in a 1 minute period. **NOTE** `enableRequestMetrics` must be set to `true` to create this alarm.

     - EvaluationPeriods (*Optional*) - The number of periods over which data is compared to the specified threshold. Defaults to 1.
     - High (*Optional*) - Threshold for creating a High Dash Event
     - Medium (*Optional*) - Threshold for creating a Medium Dash Event
     - Low (*Optional*) - Threshold for creating a Low Dash Event1.

   - ReplicationLatency (\*Optional) - The maximum number of seconds by which the replication destination Region is behind the source Region for a given replication rule. **NOTE** `crossRegion` must be configured to create this alarm.

     - EvaluationPeriods (*Optional*) - The number of periods over which data is compared to the specified threshold. Defaults to 1.
     - High (*Optional*) - Threshold for creating a High Dash Event
     - Medium (*Optional*) - Threshold for creating a Medium Dash Event
     - Low (*Optional*) - Threshold for creating a Low Dash Event1.

1. tags (*Optional*) - A list of additional tags

1. encryptionKey (*Optional*) - Set to use a custom KMS key for encryption instead of using the default SWA key. Provide the alias of the key.

1. crossAccountReplication (*Optional*) - provide only if you are configuring bucket for S3 replication

   - enableAsDestinationOrSource  (*Required* if crossAccountReplicationType is defined) - Configures the bucket as either a source or destination. Accepted values are `source` and `destination`.

1. inventoryConfigurations (*Optional*) - If defined, specifies the list of S3 Inventory configurations for the
   bucket.

   a. id (*Required*) - Unique identifier for the inventory configuration. Used for *Id* in [InventoryConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-inventoryconfiguration.html#cfn-s3-bucket-inventoryconfiguration-id)

   b. destinationBucketArn (*required*) - The Amazon Resource Name (ARN) of the bucket to which data is exported. Used for *BucketArn* in [InventoryConfiguration Destination](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-destination.html#cfn-s3-bucket-destination-bucketarn)

   c. format (*required*) - Specifies the file format used when exporting data to Amazon S3. Used for *ExpirationInDays* in [InventoryConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-destination.html#cfn-s3-bucket-destination-format)

   d. destinationPrefix (*Optional*) - The prefix to use when exporting data. The prefix is prepended to all results. Used for *Prefix* in \[InventoryConfiguration\](<https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-destination.html#cfn-s3-bucket-destination-prefix>

   e. enabled (*Required*) - Specifies whether the inventory is enabled or disabled. If set to True, an inventory list is generated. If set to False, no inventory list is generated. Used for *Enabled* in [InventoryConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-inventoryconfiguration.html#cfn-s3-bucket-inventoryconfiguration-enabled)

   f. schedule (*Required*) - Specifies the schedule for generating inventory results. Daily or Weekly. [InventoryConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-inventoryconfiguration.html#cfn-s3-bucket-inventoryconfiguration-schedulefrequency)

   g. optionalFields (*Optional*) - Contains the optional fields that are included in the inventory results. Valid values: Size | LastModifiedDate | StorageClass | ETag | IsMultipartUploaded | ReplicationStatus | EncryptionStatus | ObjectLockRetainUntilDate | ObjectLockMode | ObjectLockLegalHoldStatus | IntelligentTieringAccessTier | BucketKeyStatus [InventoryConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-inventoryconfiguration.html#cfn-s3-bucket-inventoryconfiguration-optionalfields)

1. inventoryDestination (*Optional*) - If defined, grants permissions necessary for the bucket to be used as a destination for S3 Inventory. Takes a list of the below objects.

   a. name (*Required*) - the source bucket name.

   b. sourceAccount (*Optional*) - the account the source bucket is in.

   ***NOTE:*** If configuring a destination bucket for S3 replication, a custom KMS key will be used as the default form of encryption for the bucket. Bucket replication won't work with the SWA-provisioned KMS key because the key policy needs to grant a role from the source account permission to use the key.

   - destinationFullBucketName (*Required* if enableAsDestinationOrSource is `source`) - name of the bucket to replicate objects to

   - destinationBucketAccountId (*Required* if enableAsDestinationOrSource is `source`) - account id of the destination bucket

   - destinationKeySsm (*Required* if enableAsDestinationOrSource is `source`) - SSM key path containing the KMS Key ARN the destination bucket is encrypted with. The existence of this ssm parameter is a prerequisite to configuring your bucket as a replication source.

   - destinationS3FilterPrefix: (*Required* if enableAsDestinationOrSource is `source`) - This key must be provided, but it can be left as an empty string if you wish to not provide special object filtering.

   - sourceBucketAccountId (*Required* if enableAsDestinationOrSource is `destination`) - account id where the source replication bucket exists

   - sourceBucketName: (*Required* if enableAsDestinationOrSource is `destination`) - Value the bucket source account owner must use when naming their bucket. For instance, if the destination bucket owner uses `test-one` for this field, the source bucket owner must also use this value when naming their bucket.

1. eventNotifications (Optional) - Allows user to configure event notifications to various resources

   - eventBridgeEnabled (Optional) - Allows user to enable EventBridge integration for given S3 bucket if set to 'true'

   - lambdaConfigs (Optional) - List of maps containing a resourceArn and event key for each element

   - resourceArn (Required) - Resource arn of your lambda function

   - event (Required) - Select a single [supported event type for SQS, SNS, Lambda](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-how-to-event-types-and-destinations.html#supported-notification-event-types)

   - topicConfigs (Optional) - List of maps containing a resourceArn and event key for each element

   - resourceArn (Required) - Resource arn of your SNS topic

   - event (Required) - [supported event type for SQS, SNS, Lambda](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-how-to-event-types-and-destinations.html#supported-notification-event-types)

   - queueConfigs (Optional) - List of maps containing a resourceArn and event key for each element

   - resourceArn (Required) - Resource arn of your SQS Queue

   - event (Required) - [supported event type for SQS, SNS, Lambda](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-how-to-event-types-and-destinations.html#supported-notification-event-types)

   ***NOTE:*** Your event notification destination resources must be properly configured to accept notifications from S3 prior to sending notifications to them. See resource for [troubleshooting tips](https://aws.amazon.com/premiumsupport/knowledge-center/unable-validate-destination-s3/).

1. corsRules (*Optional*) - If defined, sets CORS rules for a specified bucket

   - allowedHeaders (*Required*) (*List*) - The AllowedHeader element specifies which headers are allowed in a preflight request through the Access-Control-Request-Headers header. Each header name in the Access-Control-Request-Headers header must match a corresponding entry in the rule. Amazon S3 will send only the allowed headers in a response that were requested.  Each origin can allow up to 1 wildcard character

   - allowedMethods (*Required*) (*List*) - The S3 operations you would like to allow on this bucket. Pick from GET, PUT, POST, DELETE, HEAD

   - allowedOrigins (*Required*) (*List*) - What URL's are allowed to perform the above actions. Each origin can allow up to 1 wildcard character

   - exposeHeaders (*Optional*) (*List*) - Allows for a header in the response that you want the calling application to be able to access. This defaults to none if not defined.

   - maxAge (*Required*) (*Int*) - Specifies the time in seconds that your browser can cache the response for a preflight request

   - Sample Configuration

     ```yaml
     - name: test-cors-rules
       versioning: Enabled
       enableServerAccessLogging: "true"
       enableRequestMetrics: "true"
       crossRegion: us-west-2
       encryptionKey: my_custom_key_alias
       lifecycleRules:
         - id: ArchiveRule
           status: Enabled
           transitions:
             - storage: GLACIER
               days: 90
             - storage: DEEP_ARCHIVE
               days: 180
       corsRules:
         - allowedHeaders:
             - '*'
           allowedMethods:
             - 'GET'
             - 'PUT'
           allowedOrigins:
             - 'http://localhost:3000'
           maxAge: 60
     ```

1. bucket_policy (*Optional*) - If defined, adds additional bucket policies to the deployed bucket. Takes a list of the below objects. Each object becomes a statement in the bucket's policy.

- sid (*Required*) - statement ID for the policy being added

- effect (*Optional*) - whether the policy will Allow or Deny the configured actions

- principal (*Required*) - the user, account, service, or other entity that is allowed or denied access the bucket as part of the statement. Must be of the form `principalType: principalName`, or `*` for wildcard. For more information on AWS Principal policy elements, see official [AWS documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html)

- actions (*Required*) - a list operations the principal will be allowed to complete on the deployed bucket

### Setting up S3 Cross Account Bucket Replication

Below are steps for setting up S3 bucket replication between different SWA accounts.

1. The destination bucket account owner will deploy and configure their bucket similar to the `test-two` bucket shown in the sample configuration below. Let's assume the destination bucket account owner uses `test-one` as their sourceBucketName.

1. Once the module has been deployed, provide the following information to source account owner:

   - Custom KMS Key ARN that is encrypting the destination S3 bucket
   - The full name of the destination bucket name. This will look similar to `{department}-{aws_region}-{namespace}-{name}`.

1. As the source bucket account, you will deploy and configure your bucket similar to the `test-one` bucket shown in the sample configuration below. Since the destination bucket account owner used `test-one` for their sourceBucketName, you must use `test-one` as your bucket name in order for these resource arns to match.

1. Use the full bucket name given by the destination account owner to use for the `destinationFullBucketName` key.

1. Take the key arn the destination bucket account owner provided and create an ssm parameter using the [ssm-param-crud](https://gitlab-tools.swacorp.com/swa-common/ccp/docker/ssm-param-crud), as an example. Enter the SSM key prefix for your `destinationKeySsm` config.

***NOTE:***
The SSM parameter must not be encrypted.

Once deployed, test your object replication to ensure it's working.

A couple things to note about S3 bucket replication with this module:

1. The account where destination bucket resides must deploy this module to configure their S3 bucket(s) for replication before the source destination account owner.
1. Replication is only supported within the same region.
1. Source and destination buckets must be within the same AWS organization.
1. Source and destination buckets must be within the same environment.
1. A custom KMS key is created for every destination bucket that is configured for replication
1. For existing S3 buckets deployed with this module, enabling replication will only replicate new objects after changes has been made. Existing objects will not get replicated.
1. Once a destination bucket has been configured for replication, be careful about reverting that change back. Doing so will delete the custom KMS key that encrypted the bucket and change back to the SWA-provisioned KMS key. If the key is deleted, it will prevent you from decrypting any objects encrypted with that key. Fortunately, KMS Keys take around 30 days to delete so be sure to re-encrypt those objects with the new key before its gone for good.
1. Understand that configuring S3 bucket replication to a destination bucket will grant the destination bucket ownership of your files once replicated. If ownership is not given, they cannot decrypt the objects. If you do not agree with that, then do not use this module or submit a pull request to offer an alternative.
1. Buckets configured as a bucket replication source are automatically encrypted with the SWA-provisioned KMS key by default.

## Output

The CloudFormation stack will output all the buckets created with the module. The exported name will be in `{StackName}-{name}Bucket` format.

## Sample Configuration

```yaml
vBucketList:
  - name: test-one
    versioning: Enabled
    enableServerAccessLogging: true
    enableRequestMetrics: true
    crossRegion: us-west-2
    lifecycleRules:
      - id: ArchiveRule
        status: Enabled
        transitions:
          - storage: GLACIER
            days: 90
          - storage: DEEP_ARCHIVE
            days: 180
    crossAccountReplication:
      enableAsDestinationOrSource: source
      destinationFullBucketName: destination-bucket-name
      destinationBucketAccountId: '111111111111'
      destinationKeySsm: /ssm/key-path
      destinationS3FilterPrefix: '/filter/prefix'
    eventNotifications:
      lambdaConfigs:
        - resourceArn: arn:aws:lambda:us-east-1:000000000000:test-replication-lambda
          event: s3:ObjectAcl:Put
        - resourceArn: arn:aws:lambda:us-east-1:000000000000:test-replication-lambda
          event: s3:Replication:OperationFailedReplication
      topicConfigs:
        - resourceArn: arn:aws:sns:us-east-1:000000000000:test-replication-sns-topic
          event: s3:ObjectCreated:Copy
        - resourceArn: arn:aws:sns:us-east-1:000000000000:test-replication-sns-topic
          event: s3:ObjectCreated:*
      queueConfigs:
        - resourceArn: arn:aws:sqs:us-east-1:000000000000:test-replication-sqs-queue
          event: s3:ObjectAcl:Put
        - resourceArn: arn:aws:sqs:us-east-1:000000000000:test-replication-sqs-queue
          event: s3:Replication:OperationFailedReplication
    Alarms:
      AssignmentGroup: Assignment Group
      Application: The Application
      4xxErrors:
        EvaluationPeriods: 1
        High: 100
        Medium: 50
        Low: 10
      5xxErrors:
        EvaluationPeriods: 1
        High: 100
        Medium: 50
        Low: 10
      DeleteRequests:
        EvaluationPeriods: 1
        High: 100
        Medium: 50
        Low: 10
      ReplicationLatency:
        EvaluationPeriods: 1
        High: 900
        Medium: 600
        Low: 300
  - name: test-two
    versioning: Enabled
    enableServerAccessLogging: true
    enableRequestMetrics: true
    crossRegion: us-west-2
    lifecycleRules:
      - id: ArchiveRule
        status: Enabled
        transitions:
          - storage: GLACIER
            days: 90
          - storage: DEEP_ARCHIVE
            days: 180
    crossAccountReplication:
      enableAsDestinationOrSource: destination
      sourceBucketAccountId: '000000000000'
      sourceBucketName: test-one
```

## Setting up S3 Cross Region Bucket Replication

Below are steps for setting up S3 bucket replication between bucket in different Regions

1. To start, deploy a destination bucket in any region as shown on the example below for us-west-2. Use multi region strategy deployment to create your bucket in us-west-2. Once the module has been deployed, provide the full name of the destination bucket. This will look similar to `{department}-{aws_region}-{namespace}-{name}`.
1. To create a bucket in us-east-1 follow configuration as shown below for source bucket example for US-EAST-1.
1. While creating the above source bucket in us-east-1, the cross-region replication is configured bidirectionally by default. You can specify the `disable_bidirectional_crr` flag to `true` if you need to configure the cross-region-replication unidirectionally; only from the source to the destination S3 bucket.

Note: The destination bucket gets created first and this can be achieved in a single deployment using the different namespace, during pipeline dev deploy stage, the namespace with destination bucket config gets triggered manually first in this case Dev1

## Delegating access control to access points

Below are steps for delegating access control to access points

1. Add AccessPointConfig: "true" to the configuration file.

## Module Sample Configuration

```yaml

##source bucket configuration file  in US-EAST-1
##intergration/environment/dev/dev0/400-s3-module.yml

vBucketList:
  - name: test-one
    versioning: Enabled
    enableServerAccessLogging: "true"
    enableRequestMetrics: "true"
    crossRegion: us-west-2
    crrDestinationBucket: ec-us-west-2-dev1-test-one-crr (destination-bucket-name)
    disable_bidirectional_crr: true
    replica_modifications: true

##Destination Bucket configuration for US-WEST-2
##intergration/environment/dev/dev1/410-s3-module.yml
vBucketList:
  - name: test-one-crr
    versioning: Enabled
    enableServerAccessLogging: "true"
    enableRequestMetrics: "true"

##sample Environment.yaml file
dev:
  dev0:
    deployments:
      - 00-main
  dev1:
    deployments:
      - 10-secondary
```

## Sample Output

If a stack `test-s3-bucket` is created with the sample configuration above, export names will list these buckets:

- test-s3-bucket-testoneBucket

## Testing

Refer to this confluence page: [Local Deployments](https://confluence-tools.swacorp.com/display/TITAN/Local+serverless+deployment+notes)

### Deploy to AWS locally

```sh
  docker-compose run test-suite-deploy
```

Make sure to tear down resources afterwards

```sh
  docker-compose run test-suite-destroy
```

### Running integration tests

```sh
  docker-compose run test-suite
```

### Running cfn-lint

```sh
  mv Dockerfile.local Dockerfile
  docker-compose run cfn-lint
```

### Running cfn-nag

```sh
  mv Dockerfile.local Dockerfile
  docker-compose run cfn-nag
```

### Running test coverage (unit tests)

1. Move Dockerfile.local to Dockerfile

```sh
  mv Dockerfile.local Dockerfile
  docker-compose build test-coverage
  docker-compose run test-coverage
```
