#!/usr/bin/env bash

# This script train classification task:
#
# Usage:
# ./scripts/train_cls.sh

IMAGE_SIZE=12
STAGE_NAME='pnet'
RECORD_ROOT='/home/dafu/workspace/FaceDetect/tf_JDAP/tfrecords'
#--image_sum=1031327 \
# pnet 1479686
python ./train/train_cls.py \
    --gpu_id='0' \
    --image_sum=1479686 \
    --logdir="./logdir/${STAGE_NAME}/${STAGE_NAME}_OHEM_0.7_shuffle_LB" \
    --loss_type='SF' \
    --is_ohem=True \
    --is_ERC=False \
    --model_prefix="./models/${STAGE_NAME}/${STAGE_NAME}_OHEM_0.7_shuffle_LB/${STAGE_NAME}" \
    --tfrecords_root="${RECORD_ROOT}/${STAGE_NAME}" \
    --tfrecords_num=4 \
    --image_size=${IMAGE_SIZE} \
    --frequent=100 \
    --batch_size=3000 \
    --end_epoch=16 \
    --lr=0.1 \
    --lr_decay_factor=0.2 \
    --optimizer='momentum' \
    --momentum=0.9
