#FROM continuumio/anaconda3
#version 1.0.0: 

FROM ubuntu:22.04
MAINTAINER Billy Law

ENV TZ=America/Canada
ENV DEBIAN_FRONTEND=noninteractive



RUN apt-get update \
&& apt-get -y install wget \
&& apt-get -y install unzip \
&& apt-get -y install g++ \
&& apt-get -y install gcc \
&& apt-get -y install make \
&& apt-get install -y valgrind \
&& apt-get install -y heaptrack \
&& apt-get install -y nano \
&& apt-get install -y libgsl-dev \
&& apt-get install -y libncurses5-dev \
&& apt-get install -y libbz2-dev \
&& apt-get install -y liblzma-dev

RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN echo 'alias python="python3"' >> ~/.bashrc
#this line is necessary for concoct due to some annoying artifact.
RUN ln -s /usr/bin/python3 /usr/bin/python

RUN pip install numpy 
RUN pip install Cython



WORKDIR /seq_cleaner_tools
RUN wget https://github.com/voutcn/megahit/releases/download/v1.2.9/MEGAHIT-1.2.9-Linux-x86_64-static.tar.gz \
&& tar zvxf MEGAHIT-1.2.9-Linux-x86_64-static.tar.gz

RUN wget https://github.com/BinPro/CONCOCT/archive/refs/tags/1.1.0.tar.gz -O concoct.tar.gz\
&& tar xzvf concoct.tar.gz 
WORKDIR /seq_cleaner_tools/CONCOCT-1.1.0
RUN python3 setup.py install

WORKDIR /seq_cleaner_tools
RUN wget http://eddylab.org/software/hmmer/hmmer.tar.gz \
&& tar -xzvf hmmer.tar.gz 
WORKDIR hmmer-3.4
RUN sh configure && make 

WORKDIR /seq_cleaner_tools
RUN wget https://github.com/hyattpd/Prodigal/archive/refs/tags/v2.6.3.zip -O prodigal.zip \
&& unzip prodigal.zip
WORKDIR Prodigal-2.6.3
RUN make 

WORKDIR /seq_cleaner_tools
RUN wget https://compsysbio.org/metawrap_mod/metawrap_modules.tar.gz \
&& tar -xzvf metawrap_modules.tar.gz

RUN wget https://compsysbio.org/metawrap_mod/metawrap_scripts.tar.gz \
&& tar -xzvf metawrap_scripts.tar.gz

WORKDIR /seq_cleaner_tools
RUN wget https://github.com/Ecogenomics/GTDBTk/archive/refs/tags/2.4.0.zip -O gtdbtk.zip \
&& unzip gtdbtk.zip 

RUN wget https://github.com/BenLangmead/bowtie2/releases/download/v2.5.3/bowtie2-2.5.3-linux-x86_64.zip -O bowtie2.zip \
&& unzip bowtie2.zip \
&& mv bowtie2-2.5.3-linux-x86_64 bowtie2

RUN wget https://github.com/samtools/samtools/releases/download/1.20/samtools-1.20.tar.bz2 -O samtools.tar.bz2 \
&& tar -xvf samtools.tar.bz2 


WORKDIR samtools-1.20
RUN sh configure \
&& make \
&& make install


# Install AdapaterRemoval
WORKDIR /seq_cleaner_tools
RUN wget https://github.com/MikkelSchubert/adapterremoval/archive/v2.1.7.tar.gz -O adapterremoval.tar.gz \
&& tar -xzvf adapterremoval.tar.gz \ 
&& mv adapterremoval-2.1.7 adapterremoval \
&& cd adapterremoval \
&& make && mv build/AdapterRemoval /seq_cleaner_tools/adapterremoval/ 


# Install CD-HIT-DUP (from auxtools)
RUN wget https://github.com/weizhongli/cdhit/releases/download/V4.6.8/cd-hit-v4.6.8-2017-1208-source.tar.gz -O cdhit.tar.gz \
&& tar --remove-files -xzvf cdhit.tar.gz \
&& rm cdhit.tar.gz \
&& mkdir cdhit_dup \ 
&& cd cd-hit-v4.6.8-2017-1208/ \ 
&& make \
&& mv cd-hit-auxtools/cd-hit-dup /seq_cleaner_tools/cdhit_dup/ \
&& cd /seq_cleaner_tools \
&& rm -r cd-hit-v4.6.8-2017-1208

WORKDIR /seq_cleaner_tools
RUN mv CONCOCT-1.1.0 concoct \
&& mv hmmer-3.4 hmmer \
&& mv Prodigal-2.6.3 prodigal \
&& mv MEGAHIT-1.2.9-Linux-x86_64-static megahit \
&& mv samtools-1.20 samtools \
&& mv GTDBTk-2.4.0 gtdbtk 

WORKDIR /seq_cleaner_tools
RUN wget http://compsysbio.org/seq_cleaner_deps/BBMap_39.06.tar.gz -O bbmap.tar.gz \
&& tar --remove-files -xzvf bbmap.tar.gz

RUN pip install psutil
RUN apt-get update && apt install -y default-jre


WORKDIR /seq_cleaner_tools
RUN rm *.tar.gz \
&& rm *.zip \
&& rm *.bz2

RUN chmod -R 777 /seq_cleaner_tools

RUN apt-get install -y python-profiler

WORKDIR /seq_cleaner

RUN wget https://raw.githubusercontent.com/billytaj/seq_cleaner/develop/MetaPro_utilities.py 
RUN wget https://raw.githubusercontent.com/billytaj/seq_cleaner/develop/seq_cleaner_commands.py
RUN wget https://raw.githubusercontent.com/billytaj/seq_cleaner/develop/seq_cleaner_paths.py
RUN wget https://raw.githubusercontent.com/billytaj/seq_cleaner/develop/seq_cleaner_pipe.py
RUN wget https://raw.githubusercontent.com/billytaj/seq_cleaner/develop/seq_cleaner_stages.py

#WORKDIR /seq_cleaner/scripts
#RUN wget https://raw.githubusercontent.com/billytaj/seq_cleaner/develop/scripts/0a_Run_bbduk_trimming_filtering.sh

RUN pip install --force-reinstall -v "scikit-learn==1.1.0"

RUN pip install numpy \
&& pip install matplotlib \
&& pip install pysam \
&& pip install checkm-genome

WORKDIR /seq_cleaner_tools
RUN wget https://github.com/matsen/pplacer/releases/download/v1.1.alpha17/pplacer-Linux-v1.1.alpha17.zip -O pplacer.zip \
&& unzip pplacer.zip \
&& mv pplacer-Linux-v1.1.alpha17 pplacer \
&& rm *.zip



#for linux-only
WORKDIR /seq_cleaner_tools/checkm_data
RUN wget https://data.ace.uq.edu.au/public/CheckM_databases/checkm_data_2015_01_16.tar.gz \
&& tar -xzvf checkm_data_2015_01_16.tar.gz \
&& rm *.tar.gz

ENV CHECKM_DATA_PATH=/seq_cleaner_tools/checkm_data
ENV PATH="${PATH}:/seq_cleaner_tools/hmmer/src"
ENV PATH="${PATH}:/seq_cleaner_tools/prodigal"
ENV PATH="${PATH}:/seq_cleaner_tools/pplacer"

WORKDIR /seq_cleaner_tools
RUN apt-get install dos2unix
RUN apt-get install -y nano
RUN wget https://github.com/bxlab/metaWRAP/archive/refs/tags/v1.3.tar.gz \
&& tar -xzvf v1.3.tar.gz \
&& rm *.tar.gz

ENV PATH="${PATH}:/seq_cleaner_tools/metaWRAP-1.3/bin"

RUN apt-get install -y git-all \
&& git clone https://github.com/lh3/bwa.git \
&& cd bwa \
&& make
ENV PATH="${PATH}:/seq_cleaner_tools/bwa"



WORKDIR /seq_cleaner_tools
RUN wget https://bitbucket.org/berkeleylab/metabat/get/37db58fe3fda88f118dfdf18899d953eeac8e852.zip -O metabat.zip \
&& unzip metabat.zip \
&& mv berkeleylab-metabat-37db58fe3fda metabat \
&& cd metabat/src

#RUN git clone https://bitbucket.org/berkeleylab/metabat.git #\
#&& git checkout v2.12.1


ENV CONDA_DIR="/opt/conda"
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda
# Put conda in path so we can use conda activate
ENV PATH=$CONDA_DIR/bin:$PATH

RUN conda config --add channels defaults \
&& conda config --add channels conda-forge \
&& conda config --add channels bioconda \
&& conda config --add channels ursky

RUN conda install -y metabat2 \
&& conda install -y psutil \
&& conda install -y biopython

RUN conda install -y pandas
ENV PATH="${PATH}:/seq_cleaner_tools/bowtie2"


WORKDIR /seq_cleaner_tools/gtdbtk
RUN python3 setup.py install

#WORKDIR /seq_cleaner_tools/gtdbtk_data
#RUN wget https://data.ace.uq.edu.au/public/gtdb/data/releases/latest/auxillary_files/gtdbtk_data.tar.gz \
#&& tar -xzvf gtdbtk_data.tar.gz
ENV GTDBTK_DATA_PATH="/seq_cleaner_tools/gtdbtk_data/release214"

WORKDIR /seq_cleaner_tools/fastANI
RUN wget https://github.com/ParBLiSS/FastANI/releases/download/v1.34/fastANI-linux64-v1.34.zip \
&& unzip fastANI-linux64-v1.34.zip \
&& rm *.zip

WORKDIR /seq_cleaner_tools/fasttree
RUN wget http://www.microbesonline.org/fasttree/FastTree \
&& chmod 777 FastTree

WORKDIR /seq_cleaner_tools/mash
RUN wget https://github.com/marbl/Mash/releases/download/v2.3/mash-Linux64-v2.3.tar \
&& tar -xvf mash-Linux64-v2.3.tar \
&& mv mash-Linux64-v2.3/* . \
&& rm *.tar




WORKDIR /seq_cleaner_tools
RUN wget https://github.com/bwa-mem2/bwa-mem2/releases/download/v2.2.1/bwa-mem2-2.2.1_x64-linux.tar.bz2 \
&& tar -xf bwa-mem2-2.2.1_x64-linux.tar.bz2 



WORKDIR /seq_cleaner_tools

#RUN wget https://github.com/ablab/spades/releases/download/v4.0.0/SPAdes-4.0.0-Linux.tar.gz \
#&& tar -xzf SPAdes-4.0.0-Linux.tar.gz \
#&& mv SPAdes-4.0.0-Linux SPAdes \
#&& rm *.tar.gz \
#&& rm *.tar.bz2
RUN apt-get update \
&& apt-get install -y cmake \
&& apt-get install -y zlib1g-dev \
&& apt-get install -y libbz2-dev

RUN wget https://github.com/ablab/spades/archive/refs/tags/v4.0.0.zip \
&& unzip v4.0.0.zip \
&& mv spades-4.0.0 SPAdes

WORKDIR SPAdes


RUN sh spades_compile.sh


#WORKDIR SPAdes

#RUN sh spades_compile.sh
#RUN sh "PREFIX=/seq_cleaner_tools/SPAdes" spades_compile.sh

#RUN conda install -y spades
#RUN wget https://github.com/ablab/spades/releases/download/v4.0.0/SPAdes-4.0.0-Linux.tar.gz \
#&& tar -xzf SPAdes-4.0.0-Linux.tar.gz \
#&& mv SPAdes-4.0.0-Linux SPAdes \
#&& rm *.tar.gz
ENV PATH="${PATH}:/seq_cleaner_tools/SPAdes/bin"
WORKDIR /seq_cleaner_tools
RUN chmod -R 777 /seq_cleaner_tools/SPAdes



RUN apt-get update \
&& apt-get install -y -qq build-essential libgsl0-dev bedtools mummer samtools

#RUN rm *.tar.gz
#RUN pip uninstall pandas
#RUN pip install --force-reinstall -v pandas==1.0.0 
#RUN pip install --force-reinstall -v 'pandas==0.13.0'

#RUN conda install -y bioconda::maxbin2
#RUN wget http://compsysbio.org/seq_cleaner_deps/MaxBin-2.2.7.tar.gz \
#&& tar -xzvf MaxBin-2.2.7.tar.gz \
#&& rm *.gz \
#&& mv MaxBin-2.2.7 maxbin

#RUN wget https://github.com/edgraham/BinSanity/archive/refs/tags/v0.5.3.zip \
#&& unzip v0.5.3.zip \
#&& mv BinSanity-0.5.3 binsanity
#RUN pip install scikit-learn
#ENV PATH="${PATH}:/seq_cleaner_tools/binsanity/bin"


#RUN wget http://compsysbio.org/seq_cleaner_deps/subread-2.0.6-Linux-x86_64.tar.gz -O subread.tar.gz \
#&& tar -xzvf subread.tar.gz \
#&& mv subread-2.0.6-Linux-x86_64 subread \
#&& rm *.gz 

#ENV PATH="${PATH}:/seq_cleaner_tools/subread/bin"

RUN apt-get update \
&& apt-get install perl
RUN export LC_ALL=en_US.UTF-8
RUN export LANG=en_US.UTF-8
RUN apt-get clean && apt-get update && apt-get install -y locales
RUN locale-gen en_US.UTF-8

RUN conda install -y bioconda::maxbin2
RUN wget http://biopython.org/DIST/biopython-1.76.tar.gz \
&& tar -xzvf biopython-1.76.tar.gz \
&& rm *.tar.* 

RUN wget https://bootstrap.pypa.io/pip/2.7/get-pip.py \
&& python2 get-pip.py

RUN apt-get install -y python2-dev
RUN pip2 install numpy
RUN pip2 install --force-reinstall biopython==1.63

RUN pip2 install matplotlib

RUN apt-get install -y python-tk


#RUN cd biopython-1.76 \
#&& python2 setup.py install

RUN wget https://github.com/bluenote-1577/skani/releases/download/latest/skani \
&& chmod 777 skani

ENV PATH="${PATH}:/seq_cleaner_tools"
RUN wget http://www.microbesonline.org/fasttree/FastTreeMP \
&& chmod 777 FastTreeMP
ENV PATH="${PATH}:/seq_cleaner_tools/FastTreeMP"


WORKDIR /seq_cleaner_tools
RUN rm *.zip
RUN wget https://github.com/COMBINE-lab/salmon/releases/download/v1.10.0/salmon-1.10.0_linux_x86_64.tar.gz \
&& tar -xzvf salmon-1.10.0_linux_x86_64.tar.gz \
&& rm *.tar.gz


ENV PATH="${PATH}:/seq_cleaner_tools/salmon-latest_linux_x86_64/bin"
ENV PATH="${PATH}:/seq_cleaner_tools/fastANI"
ENV PATH="${PATH}:/seq_cleaner_tools/fasttree"
ENV PATH="${PATH}:/seq_cleaner_tools/mash"
ENV PATH="${PATH}:/seq_cleaner_tools/adapterremoval"
ENV PATH="${PATH}:/seq_cleaner_tools/cdhit_dup"
ENV PATH="${PATH}:/seq_cleaner_tools/megahit/bin"



WORKDIR /seq_cleaner_pipe

RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/seq_cleaner_pipe.py
RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/seq_cleaner_commands.py
RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/MetaPro_utilities.py
RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/seq_cleaner_stages.py
RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/seq_cleaner_paths.py

RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/Config.ini


WORKDIR /seq_cleaner_pipe/scripts


RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/scripts/contig_reconcile.py
RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/scripts/sam_sift.py
RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/scripts/clean_reads_reconcile.py

WORKDIR /seq_cleaner_pipe/modded_scripts

RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/modded_scripts/concoct_coverage_table.py
RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/modded_scripts/extract_fasta_bins.py
RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/modded_scripts/merge_cutup_clustering.py
RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/modded_scripts/print_comment.py




CMD ["bash"]
