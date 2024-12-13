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

RUN pip install psutil
RUN apt-get update && apt install -y default-jre


WORKDIR /seq_cleaner_tools
RUN rm *.tar.gz \
&& rm *.zip \
&& rm *.bz2

RUN chmod -R 777 /seq_cleaner_tools

RUN apt-get install -y python-profiler


#WORKDIR /seq_cleaner/scripts
#RUN wget https://raw.githubusercontent.com/billytaj/seq_cleaner/develop/scripts/0a_Run_bbduk_trimming_filtering.sh

RUN pip install --force-reinstall -v "scikit-learn==1.1.0"

RUN pip install numpy \
&& pip install matplotlib \
&& pip install pysam \
&& pip install checkm-genome



RUN apt-get install -y git-all \
&& git clone https://github.com/lh3/bwa.git \
&& cd bwa \
&& make
ENV PATH="${PATH}:/seq_cleaner_tools/bwa"




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


WORKDIR /seq_cleaner_tools
RUN wget https://github.com/bwa-mem2/bwa-mem2/releases/download/v2.2.1/bwa-mem2-2.2.1_x64-linux.tar.bz2 \
&& tar -xf bwa-mem2-2.2.1_x64-linux.tar.bz2 



WORKDIR /seq_cleaner_tools




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




WORKDIR /seq_cleaner_pipe

RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/seq_cleaner_pipe.py
RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/seq_cleaner_commands.py
RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/MetaPro_utilities.py
RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/seq_cleaner_stages.py
RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/seq_cleaner_paths.py

RUN wget https://raw.githubusercontent.com/ParkinsonLab/seq_cleaner/v1.0.0/Config.ini


WORKDIR /seq_cleaner_pipe/scripts






CMD ["bash"]
