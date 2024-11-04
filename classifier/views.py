from django.shortcuts import render
from django.conf import settings
from joblib import load
from fastai.vision.all import load_learner,PILImage  
import os
import requests
import cv2
import numpy as np
from django.core.files.storage import FileSystemStorage
from .forms import UploadFileForm
from django.http import JsonResponse
import pathlib
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath
searchQuery = ''
def preprocess_image(image_path, target_size=(102, 102)):  # Đảm bảo kích thước ảnh là 102x102
    if not os.path.isfile(image_path):
        raise ValueError(f"File does not exist: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Image not found or unable to read: {image_path}")
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Chuyển ảnh sang ảnh xám
    image = cv2.resize(image, target_size)  # Resize ảnh về kích thước cố định 102x102
    return image



# Hàm dự đoán bằng mô hình Fastai
def predict_image(image_path, model_path='travell_model.pkl'):
    # Convert model path to a Path object
    model_path = pathlib.Path(model_path)
    print(model_path)
    # Load the model
    learn = load_learner(model_path)

    # Open and preprocess image
    img = PILImage.create(image_path)

    # Predict label with the loaded model
    pred_class, pred_idx, probs = learn.predict(img)

    return pred_class, probs[pred_idx].item()

def simple_upload(request):
    if request.method == 'POST' and request.FILES.get('img_pre'):
        myfile = request.FILES['img_pre']
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)  # Lưu file vào thư mục media
        filename = fs.save(myfile.name, myfile)
        uploaded_file_path = fs.path(filename)  # Trả về đường dẫn hệ thống file
        return uploaded_file_path
    return None

def homePage(request):
    return render(request, 'home.html')

def getPredict(request):
    lable_name = {
        0: 'Ba Na Hills',
        1: 'Dragon Bridge',
        2: 'Linh Ung Pagoda',
        3: 'My Khe Beach'
    }
    if request.method == 'POST':
        # Bước 1: Nhận hình ảnh từ request và thực hiện dự đoán
        image_path = simple_upload(request)
        if image_path:
            try:
                print('check2')
                predicted_class, confidence = predict_image(image_path)  # Dự đoán hình ảnh
                print('check3',predicted_class)
                searchQuery = predicted_class
                predicted_label = lable_name.get(predicted_class, 'Unknown')  # Lấy nhãn dự đoán
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'error': 'No image uploaded'}, status=400)

        # Bước 2: Truyền dữ liệu vào template
        context = {
            'result': predicted_label,
            'confidence': confidence,  # Xác suất dự đoán
        }

    if request.method == 'POST':
     
        image_path = simple_upload(request)
        if image_path:
            predicted_class = predict_image(image_path)  # Dự đoán hình ảnh
            print('check',predicted_class)
            predicted_label = lable_name.get(predicted_class, 'Unknown')  # Nhận nhãn dự đoán
        else:
            return JsonResponse({'error': 'No image uploaded'}, status=400)

      
        api_key = 'AIzaSyCbtux0PfS6Aaz9svzdjV81ojYf44D3W6w'  # Thay bằng API Key của bạn
        search_engine_id = '172109979ea454d06'  # Th
        query = predicted_class
        search_url = f"https://www.googleapis.com/customsearch/v1?q={searchQuery}&key={api_key}&cx={search_engine_id}"

        try:
            response = requests.get(search_url)
            search_results = response.json().get('items', [])
        except Exception as e:
            search_results = []

        #  Lấy tọa độ từ Google Geocoding API
        geocoding_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={searchQuery}&key={api_key}"
        try:
            geo_response = requests.get(geocoding_url)
            geo_data = geo_response.json()

            if geo_data['results']:
                location = geo_data['results'][0]['geometry']['location']
                latitude = location['lat']
                longitude = location['lng']
            else:
                latitude, longitude = None, None
        except Exception as e:
            latitude, longitude = None, None

    
        context = {
            'result': searchQuery,
            'search_results': search_results,
            'latitude': latitude,
            'longitude': longitude
        }

    
        return render(request, 'result.html', context)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
