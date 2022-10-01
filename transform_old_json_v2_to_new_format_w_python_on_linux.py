#! /usr/bin/python3
import sys
import re
import json

from pprint import pprint


def format_date(dstr) :
    da = dstr.strip().split(' ')[0]
    if re.match(r'\d\d/\d\d/\d{4}', da):
        parts = da.split('/')
        da = parts[2] + parts[0] + parts[1]
    elif re.match(r'\d{4}-\d\d-\d\d', da):
        da = da.replace('-', '')

    return da


#----
# create template dict and translate fields
#----
def extract_acct_info(old_data, debug=False):
    new_data = { 'output_id': '1',
               'financial_class' : 'MVA',
               'facility_npi'  : '',
               'facility_addr2'  : '',
               'billing_provider_npi': '',
               'billing_provider_addr2': '',
               'work_comp_flag': 'N',
               'claim_type' : '837P',
               'claim_frequency': '1',
               'send_fax_number' : '888-888-8888',
               'pay_to_addr1' : 'PO BOX 740937',
               'pay_to_addr2' : '',
               'pay_to_city'  : 'ATLANTA',
               'pay_to_state' : 'GA',
               'pay_to_zip'   : '303740937'
             }
    old_2_new = {
        'cust_id': 'customer_id',
        'pat_acct': 'account_or_visit_number',
        'patient_account': 'account_or_visit_number',
        'total_charges': 'gross_charges',
        'payment': 'amount_paid',
        'balance': 'balance',
        'patient_firstname': 'patient_first_name',
        'patient_middlename': 'patient_middle_name',
        'patient_lastname': 'patient_last_name',
        'patient_phone': 'patient_phone',
        'patient_ssn': 'patient_ssn',
        'patient_dob': 'patient_dob',
        'patient_mrn': 'mrn',
        'patient_gender': 'patient_gender',
        'patient_addr1': 'patient_address_1',
        'patient_addr2': 'patient_address_2',
        'patient_city': 'patient_city',
        'patient_state': 'patient_state',
        'patient_zip': 'patient_zip5',
        'accident_date': 'accident_date',
        'accident_state': 'accident_location',
        'auto_accident_flag': 'accident_auto_indicator',
        'other_accident_flag': 'accident_other_indicator',
        'billing_provider': 'billing_provider_name',
        'billing_provider_npi': 'billing_provider_npi',
        'billing_provider_addr1': 'billing_provider_address',
        'billing_provider_city': 'billing_provider_city',
        'billing_provider_state': 'billing_provider_state',
        'billing_provider_zip': 'billing_provider_zip',
        'billing_provider_taxid': 'billing_provider_tax_id',
        'render_id': 'servicing_provider_customer_code',
        'render_npi': 'servicing_provider_npi',
        'render_taxonomy': 'servicing_provider_taxonomy',
        'render_firstname': 'servicing_provider_first_name',
        'render_middlename': 'servicing_provider_middle_name',
        'render_lastname': 'servicing_provider_last_name',
        'facility': 'servicing_provider_location_name',
        'facility_npi': 'servicing_provider_location_npi',
        'facility_code': 'place_of_service_location_code',
        'facility_addr1': 'servicing_provider_location_address',
        'facility_city': 'servicing_provider_location_city',
        'facility_state': 'servicing_provider_location_state',
        'facility_zip': 'servicing_provider_location_zip',
        'admission_date': 'admit_date_or_service_date',
        'discharge_date': 'discharge_date_or_end_service_date',
        'pay_to_name': 'billing_provider_name'
    }

    for f_new, f_old in old_2_new.items():
        try:
            new_data[f_new] = old_data[f_old]
            
            if debug == True:
                print(f"'{f_old}': '{old_data[f_old]}' --> '{f_new}': '{new_data[f_new]}'", file=sys.stderr)
        except KeyError as e:
            print(str(e), file=sys.stderr)

    #----
    # collecting ICD codes
    #----
    icd_fields = [
        "primary_diagnostic_code",
        "secondary_diagnostic_code",
        "tertiary_diagnostic_code",
        "quinary_diagnostic_code"  ]
    icd_codes = []

    for icd_fld in icd_fields:
        if len(old_data[icd_fld]) > 0:
            icd_codes.append(old_data[icd_fld])

    new_data["diagnoses"] = ','.join(icd_codes)

    new_data["billing_provider_taxid"] = new_data["billing_provider_taxid"].replace('-', '')
    new_data["patient_account"] = new_data["patient_account"].split('-')[0]
    new_data["pat_acct"]        = new_data["patient_account"]
    new_data["patient_dob"]     = format_date(new_data["patient_dob"])
    new_data["discharge_date"]  = format_date(new_data["discharge_date"])
    new_data["admission_date"]  = format_date(new_data["admission_date"])
    new_data["service_date"]    = new_data["admission_date"]

    return new_data


#----
# add more fields of medical data
#----
def extract_proc_info(new_data, old_data, proc_idx, debug=False):
    pre_fix = 'LX{:02}_'.format(proc_idx)

    item = pre_fix + 'dx_code_pointer'
    if debug == True:
        print(item, file=sys.stderr)

    if debug == True:
        print(json.dumps(new_data, indent=4, sort_keys=True), file=sys.stderr)

    diagnoses_l = new_data['diagnoses'].split(',')
    if debug == True:
        print(diagnoses_l, file=sys.stderr)

    if len(diagnoses_l) == 1:
        new_data[item] = '1'
    elif len(diagnoses_l) == 2:
        new_data[item] = '1,2'
    elif len(diagnoses_l) == 3:
        new_data[item] = '1,2,3'
    else:
        new_data[item] = '1,2,3,4'

    item = pre_fix + 'line_ctrlnum'
    new_data[item] = ''

    item = pre_fix + 'service_date'
    new_data[item] = new_data['admission_date']

    item = pre_fix + 'procedure_code'
    new_data[item] = old_data['primary_cpt_code']

    item = pre_fix + 'unit_quantity'
    new_data[item] = old_data['total_units']

    item = pre_fix + 'charge'
    new_data[item] = old_data['gross_charges']

    item = pre_fix + 'payment'
    new_data[item] = '0.0'
    
    return new_data


def main_converter(dicy):
    proc_idx = 1
    total_charges = 0.0

    dicy1 = extract_acct_info(dicy)
    dicy2 = extract_proc_info(dicy1, dicy, proc_idx)

    total_charges += float(dicy['gross_charges'])

    dicy2['total_charges'] = '{:.2f}'.format(total_charges)
    dicy2['balance']  = dicy2['total_charges']
    dicy2['payment'] = '0.0'

    return dicy2


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("need input data file name (use ./ not cat)", file=sys.stderr)
        sys.exit(0)

    data_file = sys.argv[1]

    with open(data_file, 'r') as fh:
        for line in fh:
            line = line.strip()

            if not re.match(r'\s{0,6}{', line):
                continue
            #print(line)
                
            dicy = json.loads(line)

            dicy2 = main_converter(dicy)

            print(json.dumps(dicy2))

