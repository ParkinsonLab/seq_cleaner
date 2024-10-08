#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <https://www.gnu.org/licenses/>.

#April 12, 2021
#---------------------------------------------
#MetaPro_utilities.py
#This code houses the various helper functions MetaPro uses to coordinate the multi-threaded traffic.


#Feb 13, 2024
#--------------------------------------------------------------
#Now used in Quackers Metagenomic pipe

#Sept 16, 2024:
#--------------------------------------------------------------
#now used in seq cleaner

import sys
import os
import os.path
import multiprocessing as mp
import time
import zipfile
import shutil
from datetime import datetime as dt
import psutil as psu
import subprocess as sp
import pandas as pd
#modified MetaPro utilities to better package the 


class mp_util:
    def __init__(self, output_folder_path, bypass_log_name):
        self.mp_store = []
        self.output_folder_path = output_folder_path
        self.bypass_log_name = bypass_log_name
        #self.bypass_log_name = bypass_log_name

    def check_file_integrity(self, file_path):
        if(os.path.exists(file_path)):
            if(os.path.getsize(file_path)> 0):
                return True
            
        return False

    def mem_checker(self, threshold):
        #threshold is a percentage for available memory.  
        
        mem = psu.virtual_memory()
        available_mem = mem.available
        total_mem = mem.total
        
        available_pct = 100 * available_mem / total_mem
        
        if(float(available_pct) <= float(threshold)):
            return False
        else:
            return True
            
    def mem_footprint_checker(self, count, mem_footprint):
        #assumes some pre-determinted footprint for the program in question.
        #then it doesn't let the program run
        mem = psu.virtual_memory()
        total_mem = mem.total/(1024*1024*1024)

        occupied_mem = count * mem_footprint

        max_limit = total_mem * 0.9
        if(occupied_mem > max_limit):
            return False
        else:
            return True

            
    def make_folder(self, folder_path):
        if not (os.path.exists(folder_path)):
            os.makedirs(folder_path)
            
    def delete_folder_simple(self, folder_path):
        if(os.path.exists(folder_path)):
            print(dt.today(), "Deleting:", folder_path)
            shutil.rmtree(folder_path)
            print(dt.today(), "finished deleting:", folder_path)

    def delete_folder(self, folder_path):
        if (os.path.exists(os.path.join(folder_path, "data"))):
            print("deleting", os.path.join(folder_path, "data"))
            shutil.rmtree(os.path.join(folder_path, "data"))
        else:
            print("can't delete folder: doesn't exist:", folder_path)
            
    def compress_folder(self, folder_path):
        zip_loc = os.path.join(folder_path, "data")
        z = zipfile.ZipFile(folder_path + "_data.zip", "a", zipfile.ZIP_DEFLATED)
        print("compressing interim files:", folder_path)
        for root, dirs, files in os.walk(zip_loc):
            #print("root:", root)
            #print("dirs:", dirs)
            #print("files:", files)
            #print("===============================")
            for file in files:
                z.write(os.path.join(root, file))
        z.close()
            
    def write_to_bypass_log(self, bypass_log_path, message):
        #bypass_log_path = os.path.join(folder_path, self.bypass_log_name)
        with open(bypass_log_path, "a") as bypass_log:
            bypass_log.write("\n")
            new_message = message + "\n"
            bypass_log.write(new_message)
            


    def check_bypass_log(self, out_dir, message):
        print("message used:", message)
        print("path:", out_dir)
        stop_message = "stop_" + str(message)
        bypass_keys_list = list()
        bypass_log_path = os.path.join(out_dir, self.bypass_log_name)
        if(os.path.exists(bypass_log_path)):
            with open(bypass_log_path, "r") as bypass_log:
                for line in bypass_log:
                    bypass_key = line.strip("\n")
                    bypass_keys_list.append(bypass_key)
            
            if(stop_message in bypass_keys_list):
                print(dt.today(), "stopping at:", message)
                print("to continue, remove:", stop_message, "from the bypass_log")
                sys.exit("brakes engaged")
            
            elif(message in bypass_keys_list):
                print(dt.today(), "bypassing:", message)
                return False
            
            else:
                print(dt.today(), "running:", message) 
                return True
        else:
            open(bypass_log_path, "a").close()
            print(dt.today(), "no bypass log.  running:", message)
            return True
            
    def conditional_write_to_bypass_log(self, label, stage_folder, file_name): 
        #convenience for checking if a file exists, and writing to the bypass log
        if self.check_bypass_log (self.output_folder_path, label):
            file_path = os.path.join(self.output_folder_path, stage_folder, file_name)
            if(os.path.exists(file_path)):
                self.write_to_bypass_log(self.output_folder_path, label)
        

    # Used to determine quality encoding of fastq sequences.
    # Assumes Phred+64 unless there is a character within the first 10000 reads with encoding in the Phred+33 range.
    def check_code(self, segment):
        encoding = 64
        for item in segment:
            if(ord(item) < 64):
                encoding = 33
                break
        return encoding

    def determine_encoding(self, fastq):
        #import the first 10k lines, then check the quality scores.
        #if the quality score symbols are below 76, it's phred33.  
        fastq_df = pd.read_csv(fastq, header=None, names=[None], sep="/n", skip_blank_lines = False, quoting=3, nrows=40000)
        fastq_df = pd.DataFrame(fastq_df.values.reshape(int(len(fastq_df)/4), 4))
        fastq_df.columns = ["ID", "seq", "junk", "quality"]
        quality_encoding = fastq_df["quality"].apply(lambda x: self.check_code(x)).mean() #condense into a single number.
        if(quality_encoding == 64): #all must be 64 or else it's 33
            quality_encoding = 64
        else:
            quality_encoding =  33
        return quality_encoding


    # handles where to kill the pipeline, due to the prev step behaving badly
    # logic is:  if the files inside the dep_path (or dep job label shortcut to the final_results)
    #            are empty, then there's an error.  kill the pipeline 
    def check_where_kill(self, dep_job_label=None, dep_path=None):
        if dep_job_label is None:
            if dep_path is None:
                return True
            else:
                dep_job_path = dep_path
        else:
            dep_job_path = os.path.join(dep_job_label, "final_results")

        file_list = os.listdir(dep_job_path)
        if len(file_list) > 0:
            for item in file_list:
                file_check_path = os.path.join(dep_job_path, item)
                if (os.path.getsize(file_check_path)) == 0:
                    print("empty file detected: rerunning stage")
                    sys.exit("bad dep")
            # run the job, silently
            return True
        else:
            print("stopping the pipeline.  dependencies don't exist")
            sys.exit("no dep")


    # handles where to auto-resume the pipeline on a subsequent run
    # label: used as a shorthand for paths we expect
    # full path: a bypass for when we want to use it for detecting a location that doesn't fall into the normal format (final_results)
    # dep: for checking if the job's dependencies are satisfied-> meant to point to the last stage's "final_results"
    # logic is: if the full_path has no files (or the job label shortcut to final_results)
    #           and the dependencies are ok, start the stage
    #Aug 19, 2019: There's a tweak to this:  DIAMOND will generate zero-size files, due to no-matches
    #it's allowable.
    def check_where_resume(self, job_label=None, full_path=None, dep_job_path=None, file_check_bypass = False):
        if(not file_check_bypass):
            self.check_where_kill(dep_job_path)
        if job_label:
            job_path = os.path.join(job_label, "final_results")
        else:
            job_path = full_path

        print("looking at:", job_path)

        if os.path.exists(job_path):
            file_list = os.listdir(job_path)
            if(not file_check_bypass):
                if len(file_list) > 0:
                    for item in file_list:
                        file_check_path = os.path.join(job_path, item)
                        if (os.path.getsize(file_check_path)) == 0:
                            print("empty file detected: rerunning stage")
                            return False
                    print("bypassing!")
                    return True
                else:
                    print("no files detected: running")
                    return False
            else:
                print("bypassing for special reasons")
                return True
        else:
            print("doesn't exist: running")
            return False
        
    #----------------------------------------------------------------------------------------------------------------
    #JOB LAUNCH Functions
        
    def create_and_launch(self, job_folder, inner_name, command_list):
        # create the pbs job, and launch items
        # job name: string tag for export file name
        # command list:  list of command statements for writing
        # mode: selection of which pbs template to use: default -> low memory
        # dependency_list: if not empty, will append wait args to sbatch subprocess call. it's polymorphic
        # returns back the job ID given from sbatch

        # docker mode: single cpu
        # no ID, no sbatch.  just run the command
        
        shell_script_full_path = os.path.join(self.output_folder_path, job_folder, inner_name + ".sh")

        with open(shell_script_full_path, "w") as PBS_script_out:
            for item in command_list:
                PBS_script_out.write(item + "\n")
            PBS_script_out.close()
        #if not work_in_background:
        output = ""
        try:
            sp.check_output(["sh", shell_script_full_path])#, stderr = sp.STDOUT)
        except sp.CalledProcessError as e:
            return_code = e.returncode
            if return_code != 1:
                raise
                
    def create_and_launch_v2(self, job_path, command_list):
        # create the pbs job, and launch items
        # job name: string tag for export file name
        # command list:  list of command statements for writing
        # mode: selection of which pbs template to use: default -> low memory
        # dependency_list: if not empty, will append wait args to sbatch subprocess call. it's polymorphic
        # returns back the job ID given from sbatch

        # docker mode: single cpu
        # no ID, no sbatch.  just run the command
        
        #shell_script_full_path = os.path.join(self.Output_Path, job_folder, inner_name + ".sh")

        with open(job_path, "w") as PBS_script_out:
            for item in command_list:
                PBS_script_out.write(item + "\n")
            PBS_script_out.close()
        #if not work_in_background:
        output = ""
        try:
            sp.check_output(["sh", job_path])#, stderr = sp.STDOUT)
        except sp.CalledProcessError as e:
            return_code = e.returncode
            if return_code != 1:
                raise                
                
    def launch_only(self, command_list, command_list_length):
        #just launch the job.  Don't make a script file.
        #print(dt.today(), "inside launch_only:", len(command_list))
        
        if(command_list_length == 1):
            #print("0th item:", command_list[0])
            try:
                os.system(command_list[0])
            except sp.CalledProcessError as e:
                return_code = e.returncode
                if return_code != 1:
                    raise
            #else:
            #    sys.exit("something bad happened")
        else:
        
            for command_item in command_list:
                try:
                    os.system(command_item)
                except sp.CalledProcessError as e:
                    return_code = e.returncode
                    if return_code != 1:
                        raise    




    def launch_and_create_simple(self, job_location, job_label, commands):
        #just launches a job.  no multi-process. But wait for the job to finish before continuing
        process = mp.Process(
            target=self.create_and_launch,
            args=(job_location, job_label, commands)
        )
        process.start()
        process.join()
        
    def launch_and_create_v2(self, job_path, commands):
        #just launches a job.  no multi-process.
        process = mp.Process(
            target=self.create_and_launch_v2,
            args=(job_path, commands)
        )
        process.start()
        process.join()

    def launch_and_create_v2_with_mp_store(self, job_path, commands):
        #launches a job. doesn't wait. but stores it in the mp_store queue
        process = mp.Process(
            target=self.create_and_launch_v2,
            args=(job_path, commands)
        )
        process.start()
        self.mp_store.append(process)


    def launch_and_create_with_mp_store(self, job_location, job_label, commands):
        #launches a job. doesn't wait. but stores it in the mp_store queue
        process = mp.Process(
            target=self.create_and_launch,
            args=(job_location, job_label, commands)
        )
        process.start()
        self.mp_store.append(process)

    def launch_only_simple(self, commands):
        process = mp.Process(
            target=self.launch_only,
            args=(commands, len(commands))
        )
        process.start()
        process.join()

    def launch_only_with_mp_store(self, commands):
        process = mp.Process(
            target=self.launch_only, 
            args=(commands, len(commands))
        )

        process.start()
        self.mp_store.append(process)
        
    def subdivide_and_launch(self, job_delay, mem_threshold, job_limit, job_location, job_label, commands):
        #just launches a job.  no multi-process.
        #Jan 25, 2022: now adding job controls.
        job_counter = 0
        for item in commands:
            job_name = job_label + "_" + str(job_counter)
            job_counter += 1
            job_submitted = False
            while(not job_submitted):
                if(len(self.mp_store) < job_limit):
                    if(self.mem_checker(mem_threshold)):

                        process = mp.Process(
                            target=self.create_and_launch,
                            args=(job_location, job_name, [item])
                        )
                        process.start()
                        self.mp_store.append(process)
                        print(dt.today(), job_name, "job submitted.  mem:", psu.virtual_memory().available/(1024*1024*1000), "GB", end='\r')
                        job_submitted = True
                    else:
                        time.sleep(float(job_delay))
                else:
                    self.wait_for_mp_store()
            time.sleep(float(job_delay))
        #final wait for everything to be done
        self.wait_for_mp_store()
                
        
    def launch_only_with_hold(self, mem_threshold, job_limit, job_delay, job_name, command):
        #launch a job in launch-only mode
        job_submitted = False
        while(not job_submitted):
            if(len(self.mp_store) < job_limit):
                if(self.mem_checker(mem_threshold)):
                    process = mp.Process(
                        target = self.launch_only,
                        args = (command, len(command))
                    )
                    process.start()
                    self.mp_store.append(process)
                    print(dt.today(), job_name, "job submitted.  mem:", psu.virtual_memory().available/(1024*1024*1000), "GB", end='\r')
                    job_submitted = True
                else:
                    #print(dt.today(), job_name, "Pausing. mem limit reached:", psu.virtual_memory().available/(1024*1024*1000), "GB", end='\r')
                    time.sleep(float(job_delay))
            else:
                print(dt.today(), "job limit reached.  waiting for queue to flush")
                self.wait_for_mp_store()
        time.sleep(float(job_delay))
        

    def launch_and_create_with_hold(self, mem_threshold, job_limit, job_delay, job_location, job_name, command_list):
        #launch a job in launch-with-create mode
        job_submitted = False
        while(not job_submitted):
                
            if(len(self.mp_store) < job_limit):
                if(self.mem_checker(mem_threshold)):
                    process = mp.Process(
                        target = self.create_and_launch,
                        args = (job_location, job_name, command_list)
                    )
                    process.start()
                    self.mp_store.append(process)
                    print(dt.today(), job_name, "job submitted.  mem:", psu.virtual_memory().available/(1024*1024*1000), "GB", end='\r')
                    job_submitted = True
                else:
                    #print(dt.today(), job_name, "Pausing. mem limit reached:", psu.virtual_memory().available/(1024*1024*1000), "GB", end='\r')
                    time.sleep(float(job_delay))
            else:
                print(dt.today(), "job limit reached.  waiting for queue to flush")
                self.wait_for_mp_store()
        #final wait
        #self.wait_for_mp_store()
    def launch_and_create_with_mem_footprint(self, mem_footprint, job_limit, job_location, job_name, command):
        #launch a job in launch-with-create mode
        #this controller won't be optimized for the system. It's made to keep the node from exploding.
        job_submitted = False
        
        while(not job_submitted):

            if(len(self.mp_store) < job_limit):    
                if(self.mem_footprint_checker(len(self.mp_store), mem_footprint)):
                    process = mp.Process(
                        target = self.create_and_launch,
                        args = (job_location, job_name, command)
                    )
                    process.start()
                    self.mp_store.append(process)
                    job_submitted = True
                    
                    print(dt.today(), job_name, "job submitted.  mem:", len(self.mp_store) * mem_footprint, "GB", end='\r')
                else:
                    print(dt.today(), "job limit reached.  waiting for queue to flush")
                    self.wait_for_mp_store()
            else:
                print(dt.today(), "job limit reached.  waiting for queue to flush")
                self.wait_for_mp_store()    
                

   

    #check if all jobs ran
    def check_all_job_markers(self, job_marker_list, final_folder_checklist):
        time.sleep(2)
        #if it's already been created, that means the job was killed.
        if(os.path.exists(final_folder_checklist)):
            print(dt.today(), final_folder_checklist, "exists: adding to it")
            #open it, import it.
            with open(final_folder_checklist, "r") as old_list:
                for line in old_list:
                    cleaned_line = line.strip("\n")
                    job_marker_list.append(cleaned_line)
            #then overwrite it
            with open(final_folder_checklist, "w") as checklist:
                for item in job_marker_list:
                    checklist.write(item +"\n")
                    
                for item in job_marker_list:
                    if(not os.path.exists(item)):
                        print(dt.today(), item, "not found.  kill the pipe.  restart this stage")
                        sys.exit("not all jobs completed")
            
        else:
            
            with open(final_folder_checklist, "w") as checklist:
                for item in job_marker_list:
                    checklist.write(item +"\n")
                    
                for item in job_marker_list:
                    if(not os.path.exists(item)):
                        print(dt.today(), item, "not found.  kill the pipe.  restart this stage")
                        sys.exit("not all jobs completed")

    def limited_wait_for_mp_store(self, limit):
        print(dt.today(), "limit for mp_store:", limit)
        if(len(self.mp_store) >= limit):
            print(dt.today(), "mp_store limit reached. pausing to flush")
            for item in self.mp_store:
                item.join()
            self.mp_store[:] = []
            print(dt.today(), "mp_store flushed. continuing")
    
    
    def wait_for_mp_store(self):
        print(dt.today(), "closing down processes: ", len(self.mp_store))
        count = 0
        for item in self.mp_store:
            
            print(dt.today(), "closed down: " + str(count) +  "/" + str(len(self.mp_store)) + "            ", end = "\r") 
            count += 1
            item.join()
        self.mp_store[:] = []

    def clean_or_compress(self, analysis_path, keep_all, keep_stage):
        if(keep_all == "no" and keep_stage == "no"):
            self.delete_folder(analysis_path)
        elif(keep_all == "compress" or keep_stage == "compress"):
            self.compress_folder(analysis_path)
            self.delete_folder(analysis_path)


    def launch_stage_simple(self, job_label, job_path, command_list, keep_all, keep_job):
        #wrapper for simple job launches (quality, host)
        cleanup_job_start = 0
        cleanup_job_end = 0
        print("job path:", job_path)
        
        if self.check_bypass_log(self.output_folder_path, job_label):
            print(dt.today(), "NEW CHECK running:", job_label)
            self.launch_and_create_simple(job_label, job_label, command_list)
            
            self.write_to_bypass_log(self.output_folder_path, job_label)
            cleanup_job_start = time.time()
            self.clean_or_compress(job_path, keep_all, keep_job)
            cleanup_job_end = time.time()    
        else:
            print(dt.today(), "skipping job:", job_label)

        return cleanup_job_start, cleanup_job_end
    
    def launch_stage_with_cleanup(self, command_list, marker_path, data_path, job_label, keep_all, keep_job):
        #wrapper for simple job launches (quality, host)
        cleanup_job_start = time.time()
        cleanup_job_end = time.time()
        
        if self.check_bypass_log(self.output_folder_path, job_label):
            if not os.path.exists(marker_path):
                print(dt.today(), "NEW CHECK running:", job_label)
                self.launch_and_create_simple(job_label, job_label, command_list)
                print(dt.today(), "job launched")
            #structured to catch instance where bypass isn't written, but marker is present.
            #it's not a if/else case.  Marker will be created once the job finishes.

            if os.path.exists(marker_path):
                self.write_to_bypass_log(self.output_folder_path, job_label)
                cleanup_job_start = time.time()
                self.clean_or_compress(data_path, keep_all, keep_job)
                cleanup_job_end = time.time()  
            else:
                print("error on job:", job_label)
                sys.exit("unclean exit")
              
        else:
            print(dt.today(), "skipping job:", job_label)
            cleanup_job_end = time.time() 

        return cleanup_job_start, cleanup_job_end

    def launch_with_mem_footprint(self, mem_footprint, job_limit, job_location, job_name, command):
        #launch a job in launch-with-create mode
        #this controller won't be optimized for the system. It's made to keep the node from exploding.
        job_submitted = False
        
        while(not job_submitted):

            if(len(self.mp_store) < job_limit):    
                if(self.mem_footprint_checker(len(self.mp_store), mem_footprint)):
                    process = mp.Process(
                        target = self.launch_only,
                        args = (command, len(command))
                    )
                    process.start()
                    self.mp_store.append(process)
                    job_submitted = True
                    
                    print(dt.today(), job_name, "job submitted.  mem:", len(self.mp_store) * mem_footprint, "GB", end='\r')
                else:
                    print(dt.today(), "job limit reached.  waiting for queue to flush")
                    self.wait_for_mp_store()
            else:
                print(dt.today(), "job limit reached.  waiting for queue to flush")
                self.wait_for_mp_store() 

    def launch_simple(self, command):
        process = mp.Process(
            target = self.launch_only,
            args = (command, len(command))
        )
        process.start()
        process.join()
        

