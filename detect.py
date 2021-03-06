import sys
import time
from PIL import Image, ImageDraw
from models.tiny_yolo import TinyYoloNet
from utils import *
from darknet_infrared import Darknet
from sort import Sort

def detect(cfgfile, weightfile, imgfile):
    m = Darknet(cfgfile)

    m.print_network()
    m.load_weights(weightfile)
    print('Loading weights from %s... Done!' % (weightfile))

    if m.num_classes == 20:
        namesfile = 'data/voc.names'
    elif m.num_classes == 80:
        namesfile = 'data/coco.names'
    else:
        namesfile = 'data/names'
    
    use_cuda = 1
    if use_cuda:
        m.cuda()

    img = Image.open(imgfile).convert('RGB')
    sized = img.resize((m.width, m.height))

    # for i in range(2):
    start = time.time()
    boxes = do_detect(m, sized, 0.5, 0.4, use_cuda)
    finish = time.time()
    # if i == 1:
    print('%s: Predicted in %f seconds.' % (imgfile, (finish - start)))

    class_names = load_class_names(namesfile)
    plot_boxes(img, boxes, 'predictions.jpg', class_names)

def detect_file(cfgfile, weightfile, input_file):
    m = Darknet(cfgfile)

    m.print_network()
    m.load_weights(weightfile)
    print('Loading weights from %s... Done!' % (weightfile))

    if m.num_classes == 20:
        namesfile = 'data/voc.names'
    elif m.num_classes == 80:
        namesfile = 'data/coco.names'
    else:
        namesfile = 'data/names'

    use_cuda = 1
    if use_cuda:
        m.cuda()

    with open(input_file) as file_object:
        for line in file_object:
            imgfile = line.strip()
            img = Image.open(imgfile).convert('RGB')
            sized = img.resize((m.width, m.height))

            # for i in range(2):
            start = time.time()
            boxes = do_detect(m, sized, 0.5, 0.4, use_cuda)
            finish = time.time()
                # if i == 1:
            print('%s: Predicted in %f seconds.' % (imgfile, (finish - start)))

            class_names = load_class_names(namesfile)
            image_num = os.path.splitext(os.path.split(imgfile)[1])[0]
            out_name = os.path.join('predictions', image_num + '.jpg')
            plot_boxes(img, boxes, out_name, class_names)
    save_dir = os.path.join('predictions', os.path.split(weightfile)[1] + '.pkl')
    torch.save(m, save_dir)


def detect_video_cv2(cfgfile, weightfile, videofile, tracking=False):
    import cv2
    m = Darknet(cfgfile)
    m.print_network()
    m.load_weights(weightfile)
    print('Loading weights from %s... Done!' % (weightfile))

    if m.num_classes == 20:
        namesfile = 'data/voc.names'
    elif m.num_classes == 80:
        namesfile = 'data/coco.names'
    else:
        namesfile = 'data/names'

    use_cuda = 1
    if use_cuda:
        m.cuda()
    # img = cv2.imread(videofile)
    # cv2.imshow( 'window', img)
    # cv2.waitKey(0)

    mot_tracker = Sort()
    cap = cv2.VideoCapture(videofile)
    framerate = cap.get(5)
    print('framerate is {}'.format(framerate))
    while(cap.isOpened()):
        ret, img = cap.read()
        frames = cap.get(1)
        second = frames / float(framerate)
        if frames % 300 == 0:
            print(second)
        if img is None: break
        if frames == 1:
            # video output
            # fourcc = cv2.CV_FOURCC('m', 'p', '4', 'v')
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            row, col, _ = img.shape
            sz = (col, row)
            video_save_name = os.path.splitext(os.path.split(videofile)[1])[0] + '_zz.mp4'
            # video_save_dir = os.path.join(PATH_TO_OUT, video_name + '_zz.avi')
            video = cv2.VideoWriter(video_save_name, fourcc, framerate, sz, True)


        sized = cv2.resize(img, (m.width, m.height))
        sized = cv2.cvtColor(sized, cv2.COLOR_BGR2RGB)

        # for i in range(2):
        #     start = time.time()
        boxes = do_detect(m, sized, 0.5, 0.4, use_cuda)
        if tracking:
            width = img.shape[1]
            height = img.shape[0]
            if len(boxes) != 0:
                boxes_arr = np.array(boxes)
                x1 = (boxes_arr[:, 0] - boxes_arr[:, 2] / 2.0) * width
                y1 = (boxes_arr[:, 1] - boxes_arr[:, 3] / 2.0) * height
                x2 = (boxes_arr[:, 0] + boxes_arr[:, 2] / 2.0) * width
                y2 = (boxes_arr[:, 1] + boxes_arr[:, 3] / 2.0) * height
                updata_boxes = np.stack((x1, y1, x2, y2), axis=1)
                updata_boxes = np.concatenate((updata_boxes, boxes_arr[:, 4:]), axis=1)
            else:
                updata_boxes = np.array(boxes)

            track_bbs_ids = mot_tracker.update(updata_boxes)
            boxes = track_bbs_ids.tolist()
            class_names = load_class_names(namesfile)
            image_np = plot_boxes_track(img, boxes, savename=False, class_names=class_names)
            # cv2.imshow('tmp',image_np)
            # cv2.waitKey(0)
            video.write(image_np)
        else:
            class_names = load_class_names(namesfile)
            image_np = plot_boxes_cv2(img, boxes, savename=False, class_names=class_names)
            video.write(image_np)

def detect_cv2(cfgfile, weightfile, imgfile):
    import cv2
    m = Darknet(cfgfile)

    m.print_network()
    m.load_weights(weightfile)
    print('Loading weights from %s... Done!' % (weightfile))

    if m.num_classes == 20:
        namesfile = 'data/voc.names'
    elif m.num_classes == 80:
        namesfile = 'data/coco.names'
    else:
        namesfile = 'data/names'
    
    use_cuda = 1
    if use_cuda:
        m.cuda()

    img = cv2.imread(imgfile)
    sized = cv2.resize(img, (m.width, m.height))
    sized = cv2.cvtColor(sized, cv2.COLOR_BGR2RGB)
    
    for i in range(2):
        start = time.time()
        boxes = do_detect(m, sized, 0.5, 0.4, use_cuda)
        finish = time.time()
        if i == 1:
            print('%s: Predicted in %f seconds.' % (imgfile, (finish-start)))

    class_names = load_class_names(namesfile)
    plot_boxes_cv2(img, boxes, savename='predictions.jpg', class_names=class_names)

def detect_skimage(cfgfile, weightfile, imgfile):
    from skimage import io
    from skimage.transform import resize
    m = Darknet(cfgfile)

    m.print_network()
    m.load_weights(weightfile)
    print('Loading weights from %s... Done!' % (weightfile))

    if m.num_classes == 20:
        namesfile = 'data/voc.names'
    elif m.num_classes == 80:
        namesfile = 'data/coco.names'
    else:
        namesfile = 'data/names'
    
    use_cuda = 1
    if use_cuda:
        m.cuda()

    img = io.imread(imgfile)
    sized = resize(img, (m.width, m.height)) * 255
    
    for i in range(2):
        start = time.time()
        boxes = do_detect(m, sized, 0.5, 0.4, use_cuda)
        finish = time.time()
        if i == 1:
            print('%s: Predicted in %f seconds.' % (imgfile, (finish-start)))

    class_names = load_class_names(namesfile)
    plot_boxes_cv2(img, boxes, savename='predictions.jpg', class_names=class_names)


if __name__ == '__main__':
    if len(sys.argv) == 4:
        cfgfile = sys.argv[1]
        weightfile = sys.argv[2]
        imgfile = sys.argv[3]
        # detect(cfgfile, weightfile, imgfile)
        detect_file(cfgfile, weightfile, imgfile)
        # detect_video_cv2(cfgfile, weightfile, imgfile, tracking=True)
        #detect_cv2(cfgfile, weightfile, imgfile)
        #detect_skimage(cfgfile, weightfile, imgfile)
    else:
        print('Usage: ')
        print('  python detect.py cfgfile weightfile imgfile')
        #detect('cfg/tiny-yolo-voc.cfg', 'tiny-yolo-voc.weights', 'data/person.jpg', version=1)
