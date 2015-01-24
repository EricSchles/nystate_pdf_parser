from sys import argv
import sys
import os
import pandas as pd
from subprocess import call
"""
Values:
permit type
permit id
permit issued to
facility name
facility address
facility contact
facility description

## typically on a page entitled "list of conditions" 
federally enforceable conditions

## emission information
## if page with"Facility Permissible Emissions" exists then need:
name of pollutant  # written as "Name:"
potential to emit  # written as "PTE:" or "PTE(s):" and followed by value 

## "Emission Unit Permissible Emissions"
## if page with"Emission Unit Permissible Emissions" exists then need:
emission unit  # this should match up with the same emission unit and related information in subsequent pages below
name of pollutant  # written as "Name:"
potential to emit  # written as "PTE:" or "PTE(s):" and followed by value 

## in all subsequent pages 
## information on emission units, the equipment that releases pollution into the air 

emission units  # written as "Emission Unit: [unit id here]"
emission unit description  # written as "Emission Unit Description: [description here] and follows the above
control type  # written as "Control Type:" and not always present, depends on emission unit and may repeat multiple times, we only need it once 

## information on monitoring requirements 

monitoring type  # written as "Monitoring Type:"
monitoring frequency  # written as "Monitoring Frequency:"
parameter monitored  # written as "Parameter Monitored:" and not always present, it depends on monitoring type
upper permit limit  # written as "Upper Permit Limit:" and not always present, depends on monitoring type
lower permit limit  # written as "Lower Permit Limit:" and not always present, depends on monitoring type
"""

def convert(pdf):
    call(["pdftotext","-layout",pdf])

def clean(name_text):
    to_parse = []
    with open(name_text) as f:
        for line in f:
            line = line.decode("ascii","ignore")
            line = line.replace("\n","")
            line = line.replace("\t","")
            if line != '':
                to_parse.append(line)
    return to_parse


def background_segment(cleaned):
	records = []
	record = []
	start = False

	for ind,line in enumerate(cleaned):
		first = "Permit Type" in line
		if first:
			start = True
		if start:
			record.append(line)
			first = "By acceptance of this permit, the permittee agrees that the permit" in line
			if first:
				records.append(record)
				record = []
				start = False	
		
        return records

def list_of_conditions_segment(cleaned):
	records = []
	record = []
	start = False

	for ind,line in enumerate(cleaned):
		first = "FEDERALLY ENFORCEABLE CONDITIONS" in line
		if first:
			start = True
		if start:
			record.append(line)
			first = "STATE ONLY ENFORCEABLE CONDITIONS" in line
			if first:
				records.append(record)
				record = []
				start = False	
        return records

def rest_of_file_segment(cleaned):
	records = []
	record = []
	start = False

	for ind,line in enumerate(cleaned):
		first = "STATE ONLY ENFORCEABLE CONDITIONS" in line
		if first:
			start = True
		if start:
			records.append(line)	
        return records

   	

def emission_parse(record):
    values = {
        "emission unit":[],"emission unit description":[],
        "emission unit description":[],"name of pollutant":[],
        "potential to emit":[],"process description":[]
    }
    in_range = True
    in_range_plus_ten = True
    
    for ind,line in enumerate(record):
        name_exists = False
        PTE_exists = False
        
        if "Emission Unit:" in line:
            try:
                record[ind+1]
            except IndexError:
                in_range = False
            if in_range:
        	emission_unit = line.split("Emission Unit:")[1]
        	values["emission unit"].append(emission_unit)
        	if "Process Description" in record[ind+1]:
                    values["process description"].append([record[ind+1].split("Process Description")[1],emission_unit])
        	else:
        		values["process description"].append(None)
        	if "Emission Unit Description" in record[ind+1]:
                    values["emission unit description"].append([record[ind+1].split("Emission Unit Description")[1],emission_unit])
        	else:
                    values["emission unit description"].append(None)
                try:
                    record[ind+10]
                except IndexError:
                    in_range_plus_ten = False
                if in_range_plus_ten:
                    for i in xrange(ind,ind+11):
                        if "Name:" in record[i]:
                            values["name of pollutant"].append(record[i].split("Name:")[1])
                            name_exists = True
                        if "PTE" in record[i]:
                            new_line = record[i].replace("(","")
                            new_line = new_line.replace("s","") #assumes name is upper case
                            new_line = new_line.replace(")","")
                            values["potential to emit"].append(record[i].split("PTE")[1])	
                            PTE_exists = True
                        if not name_exists:
                                values["name of pollutant"].append(None)
                        else:
                                name_exists = False
                        if not PTE_exists:
                                values["potential to emit"].append(None)
                        else:
                                PTE_exists = False
    return values




def main(pdf=None):
    if pdf== None:
        pdf = sys.argv[1]
    
    if "@" in pdf and pdf.count(".") == 2:
        name_text = pdf.split(".")[0]+"."+pdf.split(".")[1]+".txt"
        name_csv = pdf.split(".")[0]+"."+pdf.split(".")[1]+".csv" 
    else:
        name_text = pdf.split(".")[0]+".txt"
        name_csv = pdf.split(".")[0]+".csv" 

    if not os.path.exists(name_text):
        convert(pdf)
    records = []
    cleaned = clean(name_text)
             
    stuff_we_care_about = [rest_of_file_segment(cleaned),list_of_conditions_segment(cleaned), background_segment(cleaned)]
    for record in stuff_we_care_about:
    	records.append(emission_parse(record))

    df = pd.DataFrame(columns=["permit type","permit id","permit issued to","facility name","facility address","facility contact","facility description","federally enforceable conditions","name of pollutant","potential to emit","emission units","emission unit description","process description","control type","monitoring type","monitoring frequency","parameter monitored","upper permit limit","lower permit limit"])
    for record in records: df = df.append(record,ignore_index=True)
    df.to_csv(name_csv)

    
if __name__ == '__main__':
    main()
