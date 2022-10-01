import os
import sys
import json


def convert_tpliq_prebilling_record(line):
    dicy = json.loads(line)

    x = {}
    x['cust_id']    = dicy['cust_id']
    x['vx_src_sk']  = dicy['mlx_src_sk']
    x['vx_pm_sk']   = dicy['mlx_drq_pm_sk']
    x['claim_type'] = '837P'
    x['claim_frequency'] = '7'
    x['vx_carrier_claim_number'] = dicy['cms_1a_insured_id']
    x['original_ref_number']     = dicy['cms_1a_insured_id']
    x['vx_carrier_policy_number'] = dicy['insurer_policy_number']

    x['vx_carrier_name'] =  dicy['insurer_name']
    x['vx_carrier_address_1'] = dicy['insurer_address_line2']
    x['vx_carrier_address_2'] = dicy['insurer_address_line3']
    ins_city, ins_st_zip  = dicy['insurer_address_line4'].split(',', 1)
    x['vx_carrier_city'] = ins_city.strip()
    ins_state, ins_zip = ins_st_zip.strip().split(' ', 1)
    x['vx_carrier_state'] = ins_state.strip()
    x['vx_carrier_zip']  = ins_zip.replace('-', '').strip()

    x['patient_account'] = dicy['cms_26_pat_acct_number']
    x['pat_acct'] = x['patient_account']

    #-------------------------
    # patient information
    #-------------------------
    name = dicy['cms_2_patient_name'].split(',', 1)
    name = [e.strip() for e in name]
    x['patient_lastname'] = name[0]

    if ',' in name[1]  :
        x['patient_firstname'], x['patient_middlename'] = name[1].split(',', 1)
    elif ' ' in name[1]:
        x['patient_firstname'], x['patient_middlename'] = name[1].split(' ', 1)
    else:
        x['patient_firstname']  = name[1]
        x['patient_middlename'] = ''


    dob = dicy['cms_3_ccyy'] + dicy['cms_3_mm'] + dicy['cms_3_dd']
    x['patient_dob'] = dob

    if dicy['cms_3_female_ind'] in ['1', 1, 'Y', 'y', 't']:
        x['patient_gender'] = 'F'
    else:
        x['patient_gender'] = 'M'


    x['patient_addr1'] = dicy['cms_5_patient_address']
    x['patient_addr2'] = ''
    x['patient_city']  = dicy['cms_5_patient_city']
    x['patient_state'] = dicy['cms_5_patient_state']
    x['patient_zip']   = dicy['cms_5_patient_zip']
    x['patient_phone'] = dicy['cms_5_patient_phone'].replace('-','').replace(' ','')


    #insured informations
    name = dicy['cms_4_insured_name'].split(',', 1)
    name = [e.strip() for e in name]
    x['vx_carrier_insured_last_name']  = name[0]
    x['vx_carrier_insured_first_name'] = name[1]

    x['vx_carrier_policy_number'] = dicy['cms_11_insured_policy_group']
    x['vx_carrier_insured_dob']   = dicy['cms_11a_ccyy'] + dicy['cms_11a_mm'] + dicy['cms_11a_dd']
    if dicy['cms_11a_female_ind'] in ['1', 1, 'Y', 'y', 't']:
        x['vx_carrier_insured_gender'] = 'F'
    else:
        x['vx_carrier_insured_gender'] = 'M'

    x['vx_carrier_insured_addr1'] = dicy['cms_7_insured_address']
    x['vx_carrier_insured_city']  = dicy['cms_7_insured_city']
    x['vx_carrier_insured_state'] = dicy['cms_7_insured_state']
    x['vx_carrier_insured_zip']   = dicy['cms_7_insured_zip']
    x['vx_carrier_insured_phone'] = dicy['cms_7_insured_phone'].replace('-','').replace(' ','')


    x['vx_date_of_loss'] = dicy["cms_15_ccyy"] + dicy["cms_15_mm"] + dicy["cms_15_dd"]
    x['vx_accident_state'] = dicy['cms_10_place']

    if dicy['cms_10a_emp_yes_ind'] in ['1', 1, 'Y', 'y', 't']:
        x['employment_flag'] = 'Y'
        x['vx_carrier_lob'] = 'WORKER COMP'
    else:
        x['employment_flag'] = 'N'

    if dicy['cms_10b_auto_yes_ind'] in ['1', 1, 'Y', 'y', 't']:
        x['auto_accident_flag'] = 'Y'
        x['vx_carrier_lob'] = 'AUTO (PERSONAL)'
    else:
        x['auto_accident_flag'] = 'N'

    if dicy['cms_10c_other_yes_ind'] in ['1', 1, 'Y', 'y', 't']:
        x['other_accident_flag'] = 'Y'
        x['vx_carrier_lob'] = 'OTHER ACCIDENT'
    else:
        x['other_accident_flag'] = 'N'



    #Diagnoses and dc_code
    diagnoses = [ dicy['cms_21_a'],dicy['cms_21_b'],dicy['cms_21_c'],dicy['cms_21_d'],
                  dicy['cms_21_e'],dicy['cms_21_f'],dicy['cms_21_g'],dicy['cms_21_h'],
                  dicy['cms_21_i'],dicy['cms_21_j'],dicy['cms_21_k'],dicy['cms_21_l']]
    x['diagnoses'] = ','.join(filter(None, diagnoses))

    dx_code_desc = [dicy['dx_code_1'] + '|' + dicy['dx_code_desc_1'],dicy['dx_code_2'] + '|' + dicy['dx_code_desc_2'],
                    dicy['dx_code_3'] + '|' + dicy['dx_code_desc_3'],dicy['dx_code_4'] + '|' + dicy['dx_code_desc_4'],
                    dicy['dx_code_5'] + '|' + dicy['dx_code_desc_5'] ]
    x['dx_code_desc'] = '@'.join(filter(None, dx_code_desc)).strip().replace('@|','')


    x['facility_code']  = dicy['cms_24_1_b_pos']

    for i in range(1,7) :
        if not dicy[F'cms_24_{i}_a_from_ccyy']:
            break

        x[F'LX0{i}_service_date']  = dicy[F'cms_24_{i}_a_from_ccyy'] \
                                      + dicy[F'cms_24_{i}_a_from_mm'] + dicy[F'cms_24_{i}_a_from_dd']
        x[F'LX0{i}_emergency']     = dicy[F'cms_24_{i}_c_emg']
        x[F'LX0{i}_procedure_code']= dicy[F'cms_24_{i}_d_code']
        x[F'LX0{i}_modifier1']     = dicy[F'cms_24_{i}_d_mod_1']
        x[F'LX0{i}_modifier2']     = dicy[F'cms_24_{i}_d_mod_2']
        x[F'LX0{i}_modifier3']     = dicy[F'cms_24_{i}_d_mod_3']
        x[F'LX0{i}_modifier4']     = dicy[F'cms_24_{i}_d_mod_4']
        x[F'LX0{i}_unit_quantity'] = dicy[F'cms_24_{i}_g_units']
        x[F'LX0{i}_charge']        = dicy[F'cms_24_{i}_f_charge_dollars'] + '.' + dicy[F'cms_24_{i}_f_charge_decimal']

        pointer = list(dicy[F'cms_24_{i}_e_pointer'])
        list_pointer = list(range(1,len(pointer)+1))
        convert_list = [str(element) for element in list_pointer]
        x[F'LX0{i}_dx_code_pointer'] = ','.join(convert_list)

    #Render informations
    x['render_npi']       = dicy['cms_24_1_j_id_value']
    x['render_taxonomy']  = dicy['add_referring_provider_taxonomy']
    x['render_firstname'] = dicy['add_referring_provider_first_name']
    x['render_lastname']  = dicy['add_referring_provider_last_name']
    x['render_middlename']= dicy['add_referring_provider_middle_name']

    #Billing provider informations
    x['billing_provider']       = dicy['cms_33_address_line1']
    x['billing_provider_npi']   = dicy['cms_33a_value']
    x['billing_provider_taxid'] = dicy['cms_25_number'].replace('-','')

    #Facility Informations
    x['facility'] = dicy['cms_32_address_line1']
    x['facility_addr1'] = dicy['cms_32_address_line2']
    x['facility_addr2'] = ''

    split1 = dicy['cms_32_address_line3'].split(',', 1)
    x['facility_city'] = split1[0]

    f_state, f_zip = split1[-1].strip().split(' ', 1)
    x['facility_state'] = f_state.strip()
    x['facility_zip']   = f_zip.replace('-', '').strip()
    x['facility_npi']   = dicy['cms_32a_value']

    x['vx_claim_type']  = dicy['mlx_src_type']
    x['send_fax_number']= dicy['send_fax_number']

    x['total_charges']  = dicy['cms_28_charge_dollars'] + '.' + dicy['cms_28_charge_decimal']
    x['balance']        =  x['total_charges']
    x['payment']        = '0.00'

    x['pay_to_addr1']   = 'PO BOX 740937'
    x['pay_to_addr2']   = ''
    x['pay_to_city']    = 'ATLANTA'
    x['pay_to_state']   = 'GA'
    x['pay_to_zip']     = '303740937'
    x['roswell_mailbox']= "Medlytix;10800 Alpharetta Hwy,Suite 208 #773;Roswell, GA 30076-1417"

    print(json.dumps(x))


def main(tpliq_json):
    with open(tpliq_json, 'r') as fh:
        for line in fh:
            if '{' in line:
                convert_tpliq_prebilling_record(line)


if __name__ == '__main__':
    input_file = sys.argv[1]
    main(input_file)

