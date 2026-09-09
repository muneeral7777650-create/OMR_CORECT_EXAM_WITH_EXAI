import cv2
import numpy as np

# ------------------------------------------
# Load Image
# ------------------------------------------
def load_image(image_input):
    """
    تحميل الصورة سواء كانت مسار ملف (str)، أو كائن بايتات مرفوع (file-like)، أو مصفوفة numpy جاهزة.
    """
    if isinstance(image_input, np.ndarray):
        return image_input.copy()

    if hasattr(image_input, "read"):
        file_bytes = np.asarray(bytearray(image_input.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if image is None:
            raise Exception("Cannot decode uploaded image.")
        return image

    if isinstance(image_input, str):
        image = cv2.imread(image_input)
        if image is None:
            raise Exception(f"Cannot load image: {image_input}")
        return image

    raise Exception(f"Unsupported image input type: {type(image_input)}")

# ------------------------------------------
# Resize Image
# ------------------------------------------
def resize_image(
        image,
        width=1400,
        height=1000):

    return cv2.resize(
        image,
        (width, height)
    )

# ------------------------------------------
# Convert To Gray
# ------------------------------------------
def to_gray(image):

    return cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

# ------------------------------------------
# Blur Image
# ------------------------------------------
def blur_image(gray):

    return cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

# ------------------------------------------
# Threshold Image
# ------------------------------------------
def threshold_image(gray):

    thresh = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV +
        cv2.THRESH_OTSU
    )[1]

    return thresh

# ------------------------------------------
# Edge Detection
# ------------------------------------------
def detect_edges(gray):

    return cv2.Canny(
        gray,
        75,
        200
    )

# ------------------------------------------
# Order Points
# ------------------------------------------
def order_points(pts):

    rect = np.zeros(
        (4, 2),
        dtype="float32"
    )

    s = pts.sum(axis=1)

    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(
        pts,
        axis=1
    )

    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect

# ------------------------------------------
# Perspective Transform
# ------------------------------------------
def four_point_transform(
        image,
        pts):

    rect = order_points(pts)

    (tl, tr, br, bl) = rect

    widthA = np.linalg.norm(
        br - bl
    )

    widthB = np.linalg.norm(
        tr - tl
    )

    maxWidth = max(
        int(widthA),
        int(widthB)
    )

    heightA = np.linalg.norm(
        tr - br
    )

    heightB = np.linalg.norm(
        tl - bl
    )

    maxHeight = max(
        int(heightA),
        int(heightB)
    )

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    matrix = cv2.getPerspectiveTransform(
        rect,
        dst
    )

    warped = cv2.warpPerspective(
        image,
        matrix,
        (maxWidth, maxHeight)
    )

    return warped

# ------------------------------------------
# Detect Sheet
# ------------------------------------------
def detect_sheet(image):

    gray = to_gray(image)

    blur = blur_image(gray)

    edges = detect_edges(blur)

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    contours = sorted(
        contours,
        key=cv2.contourArea,
        reverse=True
    )

    for contour in contours:

        perimeter = cv2.arcLength(
            contour,
            True
        )

        approx = cv2.approxPolyDP(
            contour,
            0.02 * perimeter,
            True
        )

        if len(approx) == 4:

            return approx.reshape(
                4,
                2
            )

    raise Exception(
        "Answer sheet not found."
    )

# ------------------------------------------
# Rectify Sheet
# ------------------------------------------
def rectify_sheet(image):

    points = detect_sheet(
        image
    )

    warped = four_point_transform(
        image,
        points
    )

    warped = resize_image(
        warped,
        1400,
        1000
    )

    return warped

# ------------------------------------------
# Preprocess Sheet
# ------------------------------------------
def preprocess_sheet(image):

    warped = rectify_sheet(
        image
    )

    gray = to_gray(
        warped
    )

    thresh = threshold_image(
        gray
    )

    return warped, thresh

# ------------------------------------------
# Save Debug Image
# ------------------------------------------
def save_debug_image(
        image,
        output_path):

    cv2.imwrite(
        output_path,
        image
    )