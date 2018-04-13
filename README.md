# aws-route53-zone-data-migrator
Script for Migrating a Hosted Zone to a Different AWS Account

This script takes the output from
"aws route53 list-resource-record-sets"
and modifies it according to the instructions at:
https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-migrating.html

The resulting output can then be used as input for
"aws route53 change-resource-record-sets".

The hosted zone id of the source zone must be passed as an option so that we
can detect alias records that point to the same zone. These must be moved to
the end of the import list to make sure that the alias target exists before we
attempt to create the alias. Note that the correct order of chained aliases
(alias of an alias) is not guaranteed.