#include "yolo_detector.h"
#include <cv_bridge/cv_bridge.h>
#include <opencv2/imgproc.hpp>
#include <opencv2/imgcodecs.hpp>

YoloDetector::YoloDetector(std::shared_ptr<rclcpp::Node> node)
    : node_(std::move(node))
{
    std::string model_path =
        node_->declare_parameter<std::string>("yolo_model_path",
                                              "/home/ubuntu/yolo/yolov8n.onnx");

    try {
        net_ = cv::dnn::readNetFromONNX(model_path);
        net_.setPreferableBackend(cv::dnn::DNN_BACKEND_OPENCV);
        net_.setPreferableTarget(cv::dnn::DNN_TARGET_CPU);
    } catch (const cv::Exception &e) {
        RCLCPP_ERROR(node_->get_logger(), "Failed to load YOLO model: %s", e.what());
    }

    image_sub_ = node_->create_subscription<sensor_msgs::msg::Image>(
        "/mono/image_raw", 5,
        std::bind(&YoloDetector::imageCallback, this, std::placeholders::_1));

    det_pub_ = node_->create_publisher<vision_msgs::msg::Detection2DArray>(
        "/detections", 10);
}

void YoloDetector::imageCallback(const sensor_msgs::msg::Image::SharedPtr msg)
{
    if (net_.empty())
        return;

    cv::Mat img;
    try {
        img = cv_bridge::toCvCopy(msg, "bgr8")->image;
    } catch (const cv_bridge::Exception &e) {
        RCLCPP_ERROR(node_->get_logger(), "cv_bridge error: %s", e.what());
        return;
    }

    int input_w = 640;
    int input_h = 640;

    cv::Mat blob = cv::dnn::blobFromImage(
        img, 1.0 / 255.0, cv::Size(input_w, input_h),
        cv::Scalar(0, 0, 0), true, false);

    net_.setInput(blob);
    cv::Mat outputs = net_.forward();

    vision_msgs::msg::Detection2DArray det_array;
    det_array.header = msg->header;

    const float conf_threshold = 0.4f;
    const float nms_threshold = 0.45f;

    std::vector<cv::Rect> boxes;
    std::vector<float> scores;
    std::vector<int> class_ids;

    // Простейший разбор выхода YOLOv8 (предполагается формата Nx(5+num_classes))
    for (int i = 0; i < outputs.rows; ++i) {
        float *data = outputs.ptr<float>(i);
        float obj_conf = data[4];
        if (obj_conf < conf_threshold)
            continue;

        int num_classes = outputs.cols - 5;
        int class_id = 0;
        float max_cls_conf = 0.0f;
        for (int c = 0; c < num_classes; ++c) {
            float cls_conf = data[5 + c];
            if (cls_conf > max_cls_conf) {
                max_cls_conf = cls_conf;
                class_id = c;
            }
        }

        float conf = obj_conf * max_cls_conf;
        if (conf < conf_threshold)
            continue;

        float cx = data[0];
        float cy = data[1];
        float w  = data[2];
        float h  = data[3];

        int x = static_cast<int>((cx - w / 2.0f) * img.cols / input_w);
        int y = static_cast<int>((cy - h / 2.0f) * img.rows / input_h);
        int ww = static_cast<int>(w * img.cols / input_w);
        int hh = static_cast<int>(h * img.rows / input_h);

        boxes.emplace_back(x, y, ww, hh);
        scores.emplace_back(conf);
        class_ids.emplace_back(class_id);
    }

    std::vector<int> indices;
    cv::dnn::NMSBoxes(boxes, scores, conf_threshold, nms_threshold, indices);

    for (int idx : indices) {
        const cv::Rect &box = boxes[idx];
        int cls = class_ids[idx];
        float score = scores[idx];

        vision_msgs::msg::Detection2D det;
        det.header = msg->header;
        det.results.resize(1);
        det.results[0].hypothesis.class_id = std::to_string(cls);
        det.results[0].hypothesis.score = score;

        det.bbox.center.position.x = box.x + box.width / 2.0;
        det.bbox.center.position.y = box.y + box.height / 2.0;
        det.bbox.size_x = box.width;
        det.bbox.size_y = box.height;

        det_array.detections.push_back(det);
    }

    det_pub_->publish(det_array);
}
