#!/bin/bash

folder1=/work/ab0995/a270152/testing/run/
folder2=/work/ab0995/a270152/testing_with_intermediates/run/
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'
rm ~/esm_diff/esm_diff.out
rm differ

for model in $(ls $folder1); do
    for sim in $(ls $folder1/$model); do
        for data in {outdata,restart}/; do
            for component in $(ls $folder1/$model/$sim/$data/); do
                echo "$model/$sim/$data/$component"
                echo "============================"
                echo -e "f\n" | python ~/esm_diff/esm_diff.py $folder1/$model/$sim/$data/$component $folder2/$model/$sim/$data/$component | tee /dev/tty | grep -q "Different files"
                if [ $? -eq 0 ]; then
                    echo -e "${RED}DIFFERENT!!!!${NC}"
                    echo $model/$sim/$data/$component
                    echo $model/$sim/$data/$component >> differ
                else
                    echo -e "${GREEN}SAME!!!!${NC}"
                    echo $model/$sim/$data/$component
                fi
            done
        done
    done
done

