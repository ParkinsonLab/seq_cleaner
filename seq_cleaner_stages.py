import os
import re
import sys
import time
from datetime import datetime as dt
import seq_cleaner_commands as q_com
import seq_cleaner_utilities as mp_util


class q_stage:
    def __init__(self, out_path, path_obj, dir_obj, args_pack):
        self.path_obj = path_obj
        self.dir_obj = dir_obj
        self.bin_tools = ["cct", "mbat2", "mbin2"]
        self.start_s_path   = args_pack["s_path"]
        self.start_f_path  = args_pack["p1_path"]
        self.start_r_path  = args_pack["p2_path"]
        self.job_control = mp_util.mp_util(out_path, self.path_obj.bypass_log_name)
        self.op_mode = args_pack["op_mode"]
        self.quality_encoding = "64"
        if(self.op_mode == "single"):
            self.quality_encoding = self.job_control.determine_encoding(self.start_s_path)
        else:
            self.quality_encoding = self.job_control.determine_encoding(self.start_f_path)

        
        self.command_obj = q_com.command_obj(path_obj, dir_obj, self.quality_encoding)
        self.mspades_contig_fail = False

        if(os.path.exists(self.dir_obj.assembly_alt_contigs)):
            print(dt.today(), "metaspades contigs overrided with megahit-backup")
            self.dir_obj.assembly_contigs = self.dir_obj.assembly_alt_contigs
        
        
        

        self.hosts_bypassed = False

        

    def check_host_bypass(self):
        #checks if there are hosts. if not, trigger the bypass
        list_of_hosts = sorted(self.path_obj.config["hosts"].keys())

        if(len(list_of_hosts) == 0):
            #skip host-cleaning. move data
            self.hosts_bypassed = True 
            print(dt.today(), "no hosts used: bypassing host filter")
            if(self.op_mode == "single"):
                #self.dir_obj.host_final_s = self.dir_obj.clean_dir_final_s
                self.dir_obj.host_final_s = self.dir_obj.start_s
                
            elif(self.op_mode == "paired"):
                #self.dir_obj.host_final_f = self.dir_obj.clean_dir_final_f
                #self.dir_obj.host_final_r = self.dir_obj.clean_dir_final_r
                self.dir_obj.host_final_f = self.dir_obj.start_f
                self.dir_obj.host_final_r = self.dir_obj.start_r
    
    def low_quality_filter(self):
        if (os.path.exists(self.dir_obj.clean_dir_mkr)):
            print(dt.today(), "skipping cleaning step")
        else:
             
            command = self.command_obj.adapterremoval_command(self.quality_encoding, self.dir_obj.clean_dir_mkr)
            self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.clean_dir_job, command)
            

        self.job_control.wait_for_mp_store()
        self.job_control.write_to_bypass_log(self.path_obj.bypass_log, self.path_obj.clean_dir)

    def host_filter(self):
        #launch for each new ref path
        #walk through each host and launch a bwa job
        list_of_hosts = sorted(self.path_obj.config["hosts"].keys())

        if(len(list_of_hosts) == 0):
            #skip host-cleaning. move data
            self.hosts_bypassed = True 
            print(dt.today(), "no hosts used: bypassing host filter")
            if(self.op_mode == "single"):
                #self.dir_obj.host_final_s = self.dir_obj.clean_dir_final_s
                self.dir_obj.host_final_s = self.dir_obj.start_s
                
            elif(self.op_mode == "paired"):
                #self.dir_obj.host_final_f = self.dir_obj.clean_dir_final_f
                #self.dir_obj.host_final_r = self.dir_obj.clean_dir_final_r
                self.dir_obj.host_final_f = self.dir_obj.start_f
                self.dir_obj.host_final_r = self.dir_obj.start_r

        else:

            
            for host_key in list_of_hosts:
                
                
                host_ref_path = self.path_obj.hosts_path_dict[host_key]
                ref_basename = os.path.basename(host_ref_path)
                ref_basename = ref_basename.split(".")[0]
                host_bwa_marker_path = os.path.join(self.dir_obj.host_dir_top, ref_basename + "_host_bwa_mkr")
                
                
                if(os.path.exists(host_bwa_marker_path)):
                    print("skipping Host filter:", ref_basename)
                else:
                    command = ""
                    if(self.op_mode == "single"):
                        #command = self.command_obj.clean_reads_bwa_simple_s(host_ref_path, ref_basename, self.dir_obj.clean_dir_final_s, host_bwa_marker_path)
                        command = self.command_obj.clean_reads_bwa_simple_s(host_ref_path, ref_basename, self.dir_obj.start_s, host_bwa_marker_path)
                        #self.job_control.launch_and_create_v2_with_mp_store(script_path, command)
                    else:
                        #command = self.command_obj.clean_reads_bwa_simple_p(host_ref_path, ref_basename, self.dir_obj.clean_dir_final_f, self.dir_obj.clean_dir_final_r, host_bwa_marker_path)
                        command = self.command_obj.clean_reads_bwa_simple_p(host_ref_path, ref_basename, self.dir_obj.start_f, self.dir_obj.start_r, host_bwa_marker_path)
                        #self.job_control.launch_and_create_v2_with_mp_store(script_path, command)

                    script_path = os.path.join(self.dir_obj.host_dir_top, "host_filter_" + ref_basename + ".sh")
                    self.job_control.launch_and_create_v2_with_mp_store(script_path, command)
            
            self.job_control.wait_for_mp_store()


            
            for host_key in list_of_hosts:
                host_ref_path = self.path_obj.hosts_path_dict[host_key]
                ref_basename = os.path.basename(host_ref_path)
                ref_basename = ref_basename.split(".")[0]
                sam_sift_marker_path = os.path.join(self.dir_obj.host_dir_top, ref_basename + "_sift_mkr")
                sam_path = ""
                score_out_path = ""
                sam_name = ref_basename
                sam_path = os.path.join(self.dir_obj.host_dir_sam, sam_name + ".sam")
                
                if(self.op_mode == "single"):
                    score_out_path = os.path.join(self.dir_obj.host_dir_sam, sam_name + "_s_score_bwa.out")
                else:
                    score_out_path = os.path.join(self.dir_obj.host_dir_sam, sam_name + "_p_score_bwa.out")

                
                if(os.path.exists(sam_sift_marker_path)):
                    print(dt.today(), "skipping sam sift:", ref_basename)
                else:
                    command = self.command_obj.sift_bwa_sam_command(sam_path, score_out_path, sam_sift_marker_path)
                    script_path = os.path.join(self.dir_obj.host_dir_top, "sam_sift_" + ref_basename + ".sh")
                    self.job_control.launch_and_create_v2_with_mp_store(script_path, command)

            self.job_control.wait_for_mp_store()


            #command = self.command_obj.clean_reads_reconcile(self.dir_obj.host_dir_data, self.dir_obj.host_dir_end, self.dir_obj.clean_dir_final_s, self.dir_obj.clean_dir_final_f, self.dir_obj.clean_dir_final_r, self.dir_obj.host_recon_mkr)
            command = self.command_obj.clean_reads_reconcile(self.dir_obj.host_dir_data, self.dir_obj.host_dir_end, self.dir_obj.start_s, self.dir_obj.start_f, self.dir_obj.start_r, self.dir_obj.host_recon_mkr)
            
            self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.host_recon_job, command)
            self.job_control.wait_for_mp_store()

            self.job_control.write_to_bypass_log(self.path_obj.bypass_log, self.path_obj.host_dir)

        
    def assembly(self):
        command = ""
        if(not os.path.exists(self.dir_obj.assembly_mkr)):

            if((self.path_obj.contig_tool == "metaspades") or (self.path_obj.contig_tool == "MetaSPAdes") or (self.path_obj.contig_tool == "mspades")):
                print(dt.today(), "Choosing MetaSPADES for contig generation")
                if(self.op_mode == "single"):
                    command = self.command_obj.metaspades_command_s(self.dir_obj.host_final_s, self.quality_encoding, self.dir_obj.assembly_dir_data, self.dir_obj.assembly_mkr)
                    self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.assembly_mspades_s_job, command)
                else:
                    command = self.command_obj.metaspades_command_p(self.dir_obj.host_final_f, self.dir_obj.host_final_r, self.quality_encoding, self.dir_obj.assembly_dir_data, self.dir_obj.assembly_mkr)
                    self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.assembly_mspades_p_job, command)
                    
                self.job_control.wait_for_mp_store()

            #if not(os.path.exists(self.dir_obj.assembly_contigs)):
            #    print(dt.today(), "metaspades failed to make contigs. entering backup mode")
            elif((self.path_obj.contig_tool == "megahit") or (self.path_obj.contig_tool == "MEGAHIT") or self.path_obj.contig_tool == "mhit"):
                print(dt.today(), "choosing MEGAHIT for contig generation")
                if(self.op_mode == "single"):
                    command = self.command_obj.megahit_command_s(self.dir_obj.host_final_s, self.dir_obj.assembly_alt_dir_data, self.dir_obj.assembly_mkr)
                    self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.assembly_mhit_s_job, command)
                else:
                    command = self.command_obj.megahit_command_p(self.dir_obj.host_final_f, self.dir_obj.host_final_r, self.dir_obj.assembly_alt_dir_data, self.dir_obj.assembly_mkr)
                    self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.assembly_mhit_p_job, command)
                self.job_control.wait_for_mp_store()
                #set new contigs
                self.dir_obj.assembly_contigs = self.dir_obj.assembly_alt_contigs
        else:
            print(dt.today(), "skipping: contig assembly")


        if(not os.path.exists(self.dir_obj.assembly_bt2_idx_mkr)):
            print(dt.today(), "indexing contigs for BT2")
            print("using:", self.dir_obj.assembly_bt2_idx)
            command = self.command_obj.bowtie2_index_ref_command(self.dir_obj.assembly_contigs, self.dir_obj.assembly_bt2_idx, self.dir_obj.assembly_bt2_idx_mkr)
            self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.assembly_bwa_idx_job, command)
            self.job_control.wait_for_mp_store()
        else:
            print(dt.today(), "skipping BT2 contig indexing")
        
        if(not os.path.exists(self.dir_obj.assembly_pp_mkr)):
            command = ""
            if(self.op_mode == "single"):
                command = self.command_obj.clean_reads_bowtie2_command_s(self.dir_obj.assembly_bt2_idx, self.dir_obj.host_final_s, self.dir_obj.assembly_pp_mkr)
            else:
                command = self.command_obj.clean_reads_bowtie2_command_p(self.dir_obj.assembly_bt2_idx, self.dir_obj.host_final_f, self.dir_obj.host_final_r, self.dir_obj.assembly_pp_mkr) 
            self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.assembly_pp_job, command)
            self.job_control.wait_for_mp_store()
        else:
            print(dt.today(), "skipping BT2 align contigs")

        if(not os.path.exists(self.dir_obj.assembly_scan_sam_mkr)):
            command = self.command_obj.bt2_scan_sam(self.dir_obj.assembly_scan_sam_mkr)
            self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.assembly_scan_sam_job, command)
            self.job_control.wait_for_mp_store()
        else:
            print(dt.today(), "skipping BT2 sam/bam business")
                        



        if(not os.path.exists(self.dir_obj.assembly_reconcile_mkr)):
            command = self.command_obj.contig_reconcile(self.dir_obj.assembly_score_out, self.dir_obj.assembly_dir_data, self.dir_obj.host_final_s, self.dir_obj.host_final_f, self.dir_obj.host_final_r, self.dir_obj.assembly_reconcile_mkr)
            self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.assembly_recon_job, command)
            self.job_control.wait_for_mp_store()
        else:
            print(dt.today(), "skipping contig-read reconciliation")
        
        self.job_control.write_to_bypass_log(self.path_obj.bypass_log, self.path_obj.assembly_dir)

 

    
    def concoct_binning(self):
        #print(dt.today(), "temp holder")
        #requires adjusting headers and junk before sending off to concoct.
        #code just removes the dangling portion of the ID in each contig
        if(not os.path.exists(self.dir_obj.cct_prep_mkr)):
            command = self.command_obj.concoct_prep_command(self.dir_obj.cct_prep_mkr)
            self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.cct_prep_job_path, command)
            self.job_control.wait_for_mp_store()
        else:
            print(dt.today(), "skipping concoct prep")

        if(not os.path.exists(self.dir_obj.cct_mkr)):
            command = self.command_obj.concoct_command(self.dir_obj.cct_mkr)
            self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.cct_job_path, command)
            self.job_control.wait_for_mp_store()
        else:
            print(dt.today(), "skipping concoct binning")

        if(not os.path.exists(self.dir_obj.cct_checkm_mkr)):
            print(dt.today(), "running checkm")
            command = self.command_obj.checkm_command(self.dir_obj.cct_checkm_mkr)
            self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.cct_checkm_job_path, command)
            self.job_control.wait_for_mp_store()
        else:
            print(dt.today(), "skipping checkm")
            print(self.dir_obj.cct_checkm_mkr)
        self.job_control.write_to_bypass_log(self.path_obj.bypass_log, self.path_obj.cct_bin_dir)
            
    def metabat2_binning(self):
        print(dt.today(), "running metawrap-binning: metabat2")
        command = self.command_obj.metabat2_bin_command(self.op_mode, self.hosts_bypassed, self.dir_obj.mbat2_mkr)
        self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.mbat2_job, command)
        self.job_control.wait_for_mp_store()
        self.job_control.write_to_bypass_log(self.path_obj.bypass_log, self.path_obj.mbat2_bin_dir)


    def maxbin2_binning(self):
        print(dt.today(), "running metawrap-binning: maxbin2")
        command = self.command_obj.maxbin2_bin_command(self.op_mode, self.hosts_bypassed, self.dir_obj.mbin2_mkr)
        self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.mbin2_job, command)
        self.job_control.wait_for_mp_store()
        self.job_control.write_to_bypass_log(self.path_obj.bypass_log, self.path_obj.mbin2_bin_dir)
        

    def metawrap_bin_refine(self):
        print("running metawrap bin_refinement")
        command = self.command_obj.metawrap_bin_refinement_command(self.dir_obj.mwrap_bin_r_mkr)
        self.job_control.launch_and_create_v2_with_mp_store(self.dir_obj.mwrap_bin_r_job, command)
        self.job_control.wait_for_mp_store()
        self.job_control.write_to_bypass_log(self.path_obj.bypass_log, self.path_obj.mwrap_bin_r_dir)

    def gtdbtk_classify(self):
        print("running GTDB-tk classify")
        
        for bin_choice in self.bin_tools:
            marker_path = ""
            job_path = ""
            if(bin_choice == "cct"):
                marker_path = self.dir_obj.gtdbtk_cct_mkr
                job_path = self.dir_obj.gtdbtk_cct_job
            elif(bin_choice == "mbat2"):
                marker_path = self.dir_obj.gtdbtk_mbat2_mkr
                job_path = self.dir_obj.gtdbtk_mbat2_job
            elif(bin_choice == "mbin2"):
                marker_path = self.dir_obj.gtdbtk_mbin2_mkr
                job_path = self.dir_obj.gtdbtk_mbin2_job
            command = self.command_obj.gtdbtk_command(bin_choice, marker_path)
            self.job_control.launch_and_create_v2_with_mp_store(job_path, command)
        
        self.job_control.wait_for_mp_store()
        self.job_control.write_to_bypass_log(self.path_obj.bypass_log, self.path_obj.gtdbtk_class_dir)

    def metawrap_quant(self):
        print(dt.today(), "running metawrap quant bin")
        marker_path = ""
        job_path = ""
        for bin_choice in self.bin_tools:
            if(bin_choice == "cct"):
                marker_path = self.dir_obj.mwrap_quant_cct_mkr
                job_path = self.dir_obj.mwrap_quant_cct_job
            elif(bin_choice == "mbat2"):
                marker_path = self.dir_obj.mwrap_quant_mbat2_mkr
                job_path = self.dir_obj.mwrap_quant_mbat2_job
            elif(bin_choice == "mbin2"):
                marker_path = self.dir_obj.mwrap_quant_mbin2_mkr
                job_path = self.dir_obj.mwrap_quant_mbin2_job

            command = self.command_obj.metawrap_quantify_command(bin_choice, self.dir_obj.host_final_f, self.dir_obj.host_final_r, self.dir_obj.host_final_s, marker_path)
            self.job_control.launch_and_create_v2_with_mp_store(job_path, command)
        
        
        self.job_control.wait_for_mp_store()
        self.job_control.write_to_bypass_log(self.path_obj.bypass_log, self.path_obj.mwrap_quant_dir)