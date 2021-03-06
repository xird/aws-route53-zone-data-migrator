#!/usr/bin/python
import argparse
import json
import sys

def main(inputfile, outputfile, old_hosted_zone_id, new_hosted_zone_id, comment):
   idata = json.load(open(inputfile))

   # Set up output data structure
   odata = {}
   odata['Changes'] = []
   odata['Comment'] = comment

   # Separate list for record sets that need to go at the end of the list.
   lastChanges = []

   for ResourceRecordSet in idata['ResourceRecordSets']:
      Change = {}
      Change['Action'] = "CREATE"
      Change['ResourceRecordSet'] = ResourceRecordSet

      # Following records are not migrated:
      # - Domain top level NS records
      # - SOA records
      toBeMigrated = True

      if ResourceRecordSet['Type'] == "SOA":
        toBeMigrated = False

      if ResourceRecordSet['Type'] == "NS":
        if len(ResourceRecordSet['Name'].split(".")) == 3:
          toBeMigrated = False

      if toBeMigrated:
         # Any alias records that point to this Hosted Zone must be moved to the
         # bottom of the list, to make sure that the alias target is defined
         # before the alias.
         if "AliasTarget" in ResourceRecordSet:
            if ResourceRecordSet['AliasTarget']['HostedZoneId'] == old_hosted_zone_id:
               Change['ResourceRecordSet']['AliasTarget']['HostedZoneId'] = new_hosted_zone_id
               lastChanges.append(Change)
            else:
               odata['Changes'].append(Change)
         elif "TrafficPolicyInstanceId" in ResourceRecordSet:
            # Traffic policy instances can not be migrated; Notify user about
            # this record being skipped.
            print "WARNING: Traffic policy record \"" + ResourceRecordSet['Name'] + "\" was omitted from output. Re-create the record manually after import."
         else:
            odata['Changes'].append(Change)

   for lastChange in lastChanges:
      odata['Changes'].append(lastChange)

   if len(odata['Changes']) > 1000:
      print "WARNING: The output file contains over 1000 records. The file must be manually split into files with no more than 1000 records each before using them as input for awscli."

   with open(outputfile, 'w') as outfile:
      json.dump(odata, outfile)


if __name__ == "__main__":
   helptext = """This script takes the output from
   "aws route53 list-resource-record-sets"
   and modifies it according to the instructions at:
   https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-migrating.html

   The resulting output can then be used as input for
   "aws route53 change-resource-record-sets".

   The hosted zone id of the source zone must be passed as an option so that we
   can detect alias records that point to the same zone. These must be moved to
   the end of the import list to make sure that the alias target exists before we
   attempt to create the alias. Note that the correct order of chained aliases
   (alias of an alias) is not guaranteed."""

   parser = argparse.ArgumentParser(description=helptext)
   parser.add_argument('-i', help='Input file name. Generated by "aws route53 list-resource-record-sets"', required=True, metavar="inputfile")
   parser.add_argument('-o', help='Output file name. Used as input for aws route53 change-resource-record-sets', required=True, metavar="outputfile")
   parser.add_argument('-z', help='Old hosted zone id. The id of the hosted zone described by -i', required=True, metavar="zoneidold")
   parser.add_argument('-n', help='New hosted zone id. The id of the hosted zone to be written to the output file', required=True, metavar="zoneidnew")
   parser.add_argument('-c', help='Comment for the import file. Optional comment added into the output file\'s Comment field.', default="", metavar="comment")
   args = parser.parse_args()

   main(args.i, args.o, args.z, args.n, args.c)
