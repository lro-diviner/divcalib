#! /bin/sh

file=$1

for i in `cat $file`

do
    python /u/bandfield/joshband/div_l1a_fix/div_l1a_fix.py ${i}

    echo ${i}.corrected

    head -n +8 ${i} > /tmp/l1a_fix_head
    tail -n +9 ${i} | cut -d, -f1-59 | sed 's/$/,/g' > /tmp/l1a_fix_tail
    paste -d" " /tmp/l1a_fix_tail ${i}.corrected > /tmp/l1a_fix_data
    cat /tmp/l1a_fix_head /tmp/l1a_fix_data > ${i}.corrected

done

rm /tmp/l1a_fix_head /tmp/l1a_fix_data /tmp/l1a_fix_tail

