import cv2
import numpy as np
import numpy.random as npr
# if sys.version_info[0] == 2:
#     import Queue as queue
# elif sys.version_info[0] == 3:
#     import queue


def IoU(box, boxes):
    """Compute IoU between detect box and gt boxes
    Args:
    box: numpy array , shape (5, ): x1, y1, x2, y2, score
        input box
    boxes: numpy array, shape (n, 4): x1, y1, x2, y2
        input ground truth boxes
    Returns:
        iou: numpy.array, shape (n, )
    """
    box_area = (box[2] - box[0] + 1) * (box[3] - box[1] + 1)
    area = (boxes[:, 2] - boxes[:, 0] + 1) * (boxes[:, 3] - boxes[:, 1] + 1)
    xx1 = np.maximum(box[0], boxes[:, 0])
    yy1 = np.maximum(box[1], boxes[:, 1])
    xx2 = np.minimum(box[2], boxes[:, 2])
    yy2 = np.minimum(box[3], boxes[:, 3])

    # compute the width and height of the bounding box
    w = np.maximum(0, xx2 - xx1 + 1)
    h = np.maximum(0, yy2 - yy1 + 1)

    inter = w * h
    iou = inter / (box_area + area - inter)
    return iou


def convert_to_square(bbox):
    """Convert bbox to square

    Args:
    bbox: numpy array , shape n x 5
        input bbox

    Returns
        square bbox
    """
    square_bbox = bbox.copy()

    h = bbox[:, 3] - bbox[:, 1] + 1
    w = bbox[:, 2] - bbox[:, 0] + 1
    max_side = np.maximum(h,w)
    square_bbox[:, 0] = bbox[:, 0] + w*0.5 - max_side*0.5
    square_bbox[:, 1] = bbox[:, 1] + h*0.5 - max_side*0.5
    square_bbox[:, 2] = square_bbox[:, 0] + max_side - 1
    square_bbox[:, 3] = square_bbox[:, 1] + max_side - 1
    return square_bbox


def py_nms(dets, thresh, mode="Union"):
    """
    greedily select boxes with high confidence
    keep boxes overlap <= thresh
    rule out overlap > thresh
    :param dets: [[x1, y1, x2, y2 score]]
    :param thresh: retain overlap <= thresh
    :return: indexes to keep
    """
    x1 = dets[:, 0]
    y1 = dets[:, 1]
    x2 = dets[:, 2]
    y2 = dets[:, 3]
    scores = dets[:, 4]

    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        if mode == "Union":
            ovr = inter / (areas[i] + areas[order[1:]] - inter)
        elif mode == "Minimum":
            ovr = inter / np.minimum(areas[i], areas[order[1:]])

        inds = np.where(ovr <= thresh)[0]
        order = order[inds + 1]

    return keep


def pad(bboxes, w, h):
    """
        pad the the bboxes, alse restrict the size of it
    Parameters:
    ----------
        bboxes: numpy array, n x 5
            input bboxes
        w: float number
            width of the input image
        h: float number
            height of the input image
    Returns :
    ------
        dy, dx : numpy array, n x 1
            start point of the bbox in target image
        edy, edx : numpy array, n x 1
            end point of the bbox in target image
        y, x : numpy array, n x 1
            start point of the bbox in original image
        ex, ex : numpy array, n x 1
            end point of the bbox in original image
        tmph, tmpw: numpy array, n x 1
            height and width of the bbox
    """
    tmpw, tmph = bboxes[:, 2] - bboxes[:, 0] + 1,  bboxes[:, 3] - bboxes[:, 1] + 1
    num_box = bboxes.shape[0]

    dx , dy = np.zeros((num_box, )), np.zeros((num_box, ))
    edx, edy = tmpw.copy()-1, tmph.copy()-1

    x, y, ex, ey = bboxes[:, 0], bboxes[:, 1], bboxes[:, 2], bboxes[:, 3]

    tmp_index = np.where(ex > w-1)
    edx[tmp_index] = tmpw[tmp_index] + w - 2 - ex[tmp_index]
    ex[tmp_index] = w - 1

    tmp_index = np.where(ey > h-1)
    edy[tmp_index] = tmph[tmp_index] + h - 2 - ey[tmp_index]
    ey[tmp_index] = h - 1

    tmp_index = np.where(x < 0)
    dx[tmp_index] = 0 - x[tmp_index]
    x[tmp_index] = 0

    tmp_index = np.where(y < 0)
    dy[tmp_index] = 0 - y[tmp_index]
    y[tmp_index] = 0

    return_list = [dy, edy, dx, edx, y, ey, x, ex, tmpw, tmph]
    return_list = [item.astype(np.int32) for item in return_list]

    return return_list


class DataPretreat(object):
    """
        Data color augment, reference to Caffe2 "image_input_op.h"
    """
    def __init__(self):
        # Resize method
        self.resize_method = [cv2.INTER_AREA, cv2.INTER_CUBIC, cv2.INTER_LINEAR]
        # Data color augment parameter
        self.saturation = 0.4
        self.brightness = 0.4
        self.contrast = 0.4

    @property
    def random_resize_method(self):
        select_method = npr.random(3).argmax()
        return self.resize_method[select_method]

    def uchar_protect(self, array):
        over_idx = np.where(array > 255)
        low_idx = np.where(array < 0)
        array[over_idx] = 255
        array[low_idx] = 0
        return array

    def to_grey(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        image = image[:, :, np.newaxis]
        image = np.repeat(image, 3, axis=2)
        return image

    def Brightness(self, image, alpha_rand=0.4):
        alpha = 1.0 + npr.uniform(-alpha_rand, alpha_rand)
        image = self.uchar_protect(image * alpha)
        return image.astype(np.uint8)


    def Contrast(self, image, alpha_rand=0.4):
        h, w, c = image.shape
        gray_mean = np.sum(0.114 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.299 * image[:, :, 2])
        gray_mean /= h * w
        alpha = 1.0 + npr.uniform(-alpha_rand, alpha_rand)
        image = self.uchar_protect(image * alpha + gray_mean * (1.0 - alpha))
        return image.astype(np.uint8)


    def Saturation(self, image, alpha_rand=0.4):
        alpha = 1.0 + npr.uniform(-alpha_rand, alpha_rand)
        gray_color = 0.114 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.299 * image[:, :, 2]
        gray_color = gray_color[:, :, np.newaxis]
        gray_color = np.repeat(gray_color, 3, axis=2)
        image = self.uchar_protect(image * alpha + gray_color * (1.0 - alpha))
        return image.astype(np.uint8)

    def ColorJitter(self, image, saturation=0.4, brightness=0.4, contrast=0.4):
        jitter_order = [0, 1, 2]
        npr.shuffle(jitter_order)
        for i in range(3):
            if jitter_order[i] == 0:
                image = self.Saturation(image, saturation)
            elif jitter_order[i] == 1:
                image = self.Brightness(image, brightness)
            else:
                image = self.Contrast(image, contrast)
        return image

# image_grey = cv2.imread("/home/dafu/Pictures/1003.jpg")
# image_rgb = cv2.imread("/home/dafu/Pictures/1001.jpg")
# image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
# image = image[:,:, np.newaxis]
# image = np.repeat(image, 3, axis=2)
# print(image.shape)
# cv2.imshow("a", image)
# cv2.waitKey(0)
# cv2.imshow("orign_g", image_grey)
# cv2.imshow("orign_r", image_rgb)
# for i in range(100):
#     # b_g = Brightness(image_grey)
#     # b_r = Brightness(image_rgb)
#     # cv2.imshow("b_g", b_g)
#     # cv2.imshow("b_r", b_r)
#     # c_g = Contrast(image_grey)
#     # c_r = Contrast(image_rgb)
#     # cv2.imshow("c_g", c_g)
#     # cv2.imshow("c_r", c_r)
#     s_g = ColorJitter(image_grey)
#     s_r = ColorJitter(image_rgb)
#     cv2.imshow("s_g", s_g)
#     cv2.imshow("s_r", s_r)
#     cv2.waitKey(0)