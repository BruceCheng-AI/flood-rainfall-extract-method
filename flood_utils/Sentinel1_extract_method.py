import ee,geemap
from Public_methods import otsu,final_mask 
#Sentinel1数据加载
def load_Sentinel1(start_date,end_date,roi):
    #加载哨兵1数据
    sentinel1 = ee.ImageCollection('COPERNICUS/S1_GRD')
    img_vh =sentinel1.filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
                 .filter(ee.Filter.eq('instrumentMode', 'IW')) \
                 .filterDate(start_date,end_date).filterBounds(roi).select('VH')
    
    img_vv =sentinel1.filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
                 .filter(ee.Filter.eq('instrumentMode', 'IW')) \
                 .filterDate(start_date,end_date).filterBounds(roi).select('VV')
    VH = ee.Image.cat([img_vh.min()]).clip(roi)
    VV = ee.Image.cat([img_vv.min()]).clip(roi)
    return VH,VV
#RefinedLee滤波
def RefinedLee(img): 
    #设定内核
    weights3 = ee.List.repeat(ee.List.repeat(1,3),3);
    kernel3 = ee.Kernel.fixed(3,3, weights3, 1, 1, False);
 
    mean3 = img.reduceNeighborhood(ee.Reducer.mean(), kernel3);
    variance3 = img.reduceNeighborhood(ee.Reducer.variance(), kernel3);
 
    #使用7x7窗户内的3x3窗户的样本来确定梯度和方向
    sample_weights = ee.List([[0,0,0,0,0,0,0], [0,1,0,1,0,1,0],[0,0,0,0,0,0,0], [0,1,0,1,0,1,0], [0,0,0,0,0,0,0], [0,1,0,1,0,1,0],[0,0,0,0,0,0,0]]);
 
    sample_kernel = ee.Kernel.fixed(7,7, sample_weights, 3,3, False);
 
    #计算取样窗口的平均值和方差，并存储为9个波段
    sample_mean = mean3.neighborhoodToBands(sample_kernel); 
    sample_var = variance3.neighborhoodToBands(sample_kernel);
 
    #确定取样窗口的4个梯度
    gradients = sample_mean.select(1).subtract(sample_mean.select(7)).abs();
    gradients = gradients.addBands(sample_mean.select(6).subtract(sample_mean.select(2)).abs());
    gradients = gradients.addBands(sample_mean.select(3).subtract(sample_mean.select(5)).abs());
    gradients = gradients.addBands(sample_mean.select(0).subtract(sample_mean.select(8)).abs());
 
    #并找到梯度带中的最大梯度
    max_gradient = gradients.reduce(ee.Reducer.max());
 
    #为最大梯度的带状像素创建一个掩码
    gradmask = gradients.eq(max_gradient);
 
    #重复的梯度带：每个梯度代表两个方向
    gradmask = gradmask.addBands(gradmask);
 
    #确定8个方向
    directions = sample_mean.select(1).subtract(sample_mean.select(4)).gt(sample_mean.select(4).subtract(sample_mean.select(7))).multiply(1);
    directions = directions.addBands(sample_mean.select(6).subtract(sample_mean.select(4)).gt(sample_mean.select(4).subtract(sample_mean.select(2))).multiply(2));
    directions = directions.addBands(sample_mean.select(3).subtract(sample_mean.select(4)).gt(sample_mean.select(4).subtract(sample_mean.select(5))).multiply(3));
    directions = directions.addBands(sample_mean.select(0).subtract(sample_mean.select(4)).gt(sample_mean.select(4).subtract(sample_mean.select(8))).multiply(4));
    #接下来的4个是前面4个的not()。
    directions = directions.addBands(directions.select(0).Not().multiply(5));
    directions = directions.addBands(directions.select(1).Not().multiply(6));
    directions = directions.addBands(directions.select(2).Not().multiply(7));
    directions = directions.addBands(directions.select(3).Not().multiply(8));

 
    #屏蔽所有不是1-8的值
    directions = directions.updateMask(gradmask);
 
    #将堆栈 "折叠 "成一个单一波段的图像（由于遮蔽，每个像素在它的方向波段中只有一个值（1-8），否则就会被遮蔽）。
    directions = directions.reduce(ee.Reducer.sum());  
 
    pal = ['ffffff','ff0000','ffff00', '00ff00', '00ffff', '0000ff', 'ff00ff', '000000'];
    #Map.addLayer(directions.reduce(ee.Reducer.sum()), {min:1, max:8, palette: pal}, 'Directions', false);
 
    sample_stats = sample_var.divide(sample_mean.multiply(sample_mean));
 
    #Calculate localNoiseVariance
    sigmaV = sample_stats.toArray().arraySort().arraySlice(0,0,5).arrayReduce(ee.Reducer.mean(), [0]);
 
    #为定向统计设置7*7内核
    rect_weights = ee.List.repeat(ee.List.repeat(0,7),3).cat(ee.List.repeat(ee.List.repeat(1,7),4));
 
    diag_weights = ee.List([[1,0,0,0,0,0,0], [1,1,0,0,0,0,0], [1,1,1,0,0,0,0], [1,1,1,1,0,0,0], [1,1,1,1,1,0,0], [1,1,1,1,1,1,0], [1,1,1,1,1,1,1]]);
 
    rect_kernel = ee.Kernel.fixed(7,7, rect_weights, 3, 3, False);
    diag_kernel = ee.Kernel.fixed(7,7, diag_weights, 3, 3, False);
 
    #使用原始核子为平均值和方差创建堆栈。用相关的方向进行屏蔽。
    dir_mean = img.reduceNeighborhood(ee.Reducer.mean(), rect_kernel).updateMask(directions.eq(1));
    dir_var = img.reduceNeighborhood(ee.Reducer.variance(), rect_kernel).updateMask(directions.eq(1));
 
    dir_mean = dir_mean.addBands(img.reduceNeighborhood(ee.Reducer.mean(), diag_kernel).updateMask(directions.eq(2)));
    dir_var = dir_var.addBands(img.reduceNeighborhood(ee.Reducer.variance(), diag_kernel).updateMask(directions.eq(2)));
 
    #并为旋转的核子添加波段
    for i in range(1,4,1):
        dir_mean = dir_mean.addBands(img.reduceNeighborhood(ee.Reducer.mean(), rect_kernel.rotate(i)).updateMask(directions.eq(2*i+1)));
        dir_var = dir_var.addBands(img.reduceNeighborhood(ee.Reducer.variance(), rect_kernel.rotate(i)).updateMask(directions.eq(2*i+1)));
        dir_mean = dir_mean.addBands(img.reduceNeighborhood(ee.Reducer.mean(), diag_kernel.rotate(i)).updateMask(directions.eq(2*i+2)));
        dir_var = dir_var.addBands(img.reduceNeighborhood(ee.Reducer.variance(), diag_kernel.rotate(i)).updateMask(directions.eq(2*i+2)));
  
    #"collapse" the stack into a single band image (due to masking, each pixel has just one value in it's directional band, and is otherwise masked)
    dir_mean = dir_mean.reduce(ee.Reducer.sum());
    dir_var = dir_var.reduce(ee.Reducer.sum());
 
    #最后生成过滤后的值
    varX = dir_var.subtract(dir_mean.multiply(dir_mean).multiply(sigmaV)).divide(sigmaV.add(1.0));
 
    b = varX.divide(dir_var);
 
    result = dir_mean.add(b.multiply(img.subtract(dir_mean)));
    return result
def S1_water_extract(start_date,end_date,roi):
    #加载VV和VH极化
    VH,VV = load_Sentinel1(start_date,end_date,roi);
    #进行RefinedLee滤波
    VH_LEE = RefinedLee(VH).arrayFlatten(coordinateLabels=[['LEE_VH']]);
    VV_LEE = RefinedLee(VV).arrayFlatten(coordinateLabels=[['LEE_VV']]);
    #根据地形去除干扰
    VH_final = final_mask(VH_LEE);
    VV_final = final_mask(VV_LEE);
    #调用OTSU获得阈值
    water_threshold_VH=otsu(VH_final,roi);
    water_threshold_VV=otsu(VV_final,roi);
    #根据阈值提取水体
    water_VH = VH_final.lt(water_threshold_VH);
    water_VV = VV_final.lt(water_threshold_VV);
    #融合VH水体和VV水体
    thresholds_counts = water_VH.addBands(water_VV).reduce(ee.Reducer.sum());
    Sentinel1_water = thresholds_counts.gte(ee.Image.constant(2)).select(['sum'],['Sentinel2_water'])
    #返回获得水体
    return Sentinel1_water.unmask()