# geemap_tools/clouds.py
import ee

def custom_mask_clouds(img, debug=False):
    """
    Aplica uma máscara de nuvens personalizada a uma imagem do Earth Engine.
    
    Suporta imagens com bandas QA_PIXEL (Landsat), SCL (Sentinel-2) ou MSK_CLDPRB (probabilidade de nuvem).
    Para Sentinel-2, utiliza a banda SCL com fallback para MSK_CLDPRB caso a máscara esteja completamente vazia.
    
    Parâmetros:
        img (ee.Image): Imagem de entrada contendo bandas de qualidade relacionadas a nuvens.
        debug (bool, opcional): Se True, imprime mensagens de depuração. Padrão é False.
    
    Retorno:
        ee.Image: Imagem com nuvens mascaradas (pixels de nuvem removidos).
    
    ----
    Apply a custom cloud mask to an Earth Engine image.
    
    Supports images with QA_PIXEL (Landsat), SCL (Sentinel-2), or MSK_CLDPRB (cloud probability) bands.
    For Sentinel-2, uses the SCL band with fallback to MSK_CLDPRB if the mask is completely empty.
    
    Args:
        img (ee.Image): Input image containing cloud-related quality bands.
        debug (bool, optional): If True, prints debug messages. Default is False.
    
    Returns:
        ee.Image: Image with clouds masked (cloud pixels removed).
    """

    bands = img.bandNames().getInfo()

    if 'QA_PIXEL' in bands:  # Landsat
        cloud_mask = img.select('QA_PIXEL').bitwiseAnd(1 << 3).eq(0)
        return img.updateMask(cloud_mask)

    elif 'SCL' in bands:  # Sentinel-2
        scl = img.select('SCL')
        cloud_mask = scl.remap([3, 8, 9, 10], [0]*4, defaultValue=1).eq(1)
        masked = img.updateMask(cloud_mask)

        try:
            test_mask = masked.mask().reduce(ee.Reducer.sum()).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=img.geometry(),
                scale=20,
                maxPixels=1e8
            ).getInfo()
            total = list(test_mask.values())[0]
            if total == 0 and 'MSK_CLDPRB' in bands:
                cloud_prob = img.select('MSK_CLDPRB')
                clear_mask = cloud_prob.lt(50)
                return img.updateMask(clear_mask)
        except Exception as e:
            if debug:
                print(f"[DEBUG] Erro ao testar máscara SCL: {e}")

        return masked

    elif 'MSK_CLDPRB' in bands:
        cloud_prob = img.select('MSK_CLDPRB')
        clear_mask = cloud_prob.lt(50)
        return img.updateMask(clear_mask)

    else:
        if debug:
            print("[DEBUG] Nenhuma banda de nuvem reconhecida.")
        return img

def get_clear_sky_percentage(img, roi, debug=False):
    """
    Calcula a porcentagem de céu claro (sem nuvens) sobre uma ROI com base na máscara de nuvem da imagem.
    
    Utiliza a função `custom_mask_clouds()` para aplicar a máscara apropriada à imagem.
    A porcentagem é obtida a partir da média da máscara binária (1 = claro, 0 = nublado) sobre a ROI.
    
    Parâmetros:
        img (ee.Image): Imagem do Earth Engine com bandas de máscara de nuvem.
        roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Região de interesse.
        debug (bool, opcional): Se True, imprime mensagens de depuração. Padrão é False.
    
    Retorno:
        float | None: Porcentagem de pixels com céu claro (0 a 100), ou None se falhar.
    
    ----
    Computes the percentage of clear sky (cloud-free) pixels over a ROI based on the image's cloud mask.
    
    Uses the `custom_mask_clouds()` function to apply the appropriate mask to the image.
    The percentage is calculated from the mean value of a binary mask (1 = clear, 0 = cloudy) over the ROI.
    
    Args:
        img (ee.Image): Earth Engine image with cloud mask bands.
        roi (ee.Geometry | ee.Feature | ee.FeatureCollection): Region of interest.
        debug (bool, optional): If True, prints debug messages. Default is False.
    
    Returns:
        float | None: Percentage of cloud-free pixels (0 to 100), or None if it fails.
    """

    try:
        band_names = img.bandNames()
        scale = 10  # padrão para Sentinel-2

        if band_names.contains('QA_PIXEL').getInfo():
            scale = 30  # Landsat
        elif band_names.contains('SCL').getInfo():
            scale = 10
        elif band_names.contains('MSK_CLDPRB').getInfo():
            scale = 20

        # Aplica máscara personalizada
        cloud_masked = custom_mask_clouds(img)

        # Obtém a primeira banda da máscara
        clear_mask = cloud_masked.mask().select(0)

        # Reduz sobre a ROI
        stats = clear_mask.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=scale,
            maxPixels=1e9
        ).getInfo()

        if not stats:
            if debug:
                print("[DEBUG] Redução retornou dicionário vazio.")
            return None

        # Pega o primeiro valor do dicionário (única banda)
        clear_mean = list(stats.values())[0]

        return round(clear_mean * 100, 1)

    except Exception as e:
        if debug:
            print(f"[DEBUG] Erro em get_clear_sky_percentage: {e}")
        return None
