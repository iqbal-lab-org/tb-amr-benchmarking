# Mykrobe publication supplementary files

Supplementary data are here: [https://www.nature.com/articles/ncomms10063#supplementary-information].

Downloaded the five files with sample to phenotype info with:

    wget https://media.nature.com/original/nature-assets/ncomms/2015/151221/ncomms10063/extref/ncomms10063-s{4,{7..10}}.txt

(4 is S. aureus, 7-10 are M. tuberculosis.)

Convert to unix format:

    ls ncomms10063-s* | xargs mac2unix


