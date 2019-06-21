#/usr/bin/env python3

import numpy
from astropy.io import fits
import os
import sys


print ("Hello World")

if __name__ == "__main__":

    hst_fn = sys.argv[1]
    print("Reading %s" % (hst_fn))

    model_fn = sys.argv[2]
    print("Reading model from %s" % (model_fn))

    output_fn = sys.argv[3]

    hst_hdu = fits.open(hst_fn)
    model_hdu = fits.open(model_fn)
    model_data = model_hdu[0].data

    fit_section = model_hdu[0].header['FITSECT']
    print(fit_section)

    x1 = int(fit_section.split("[")[1].split(":")[0])
    x2 = int(fit_section.split(":")[1].split(",")[0])
    y1 = int(fit_section.split(",")[1].split(":")[0])
    y2 = int(fit_section.split(":")[2].split("]")[0])
    print(x1,x2,y1,y2)

    cutout = hst_hdu['SCI'].data[y1-1:y2, x1-1:x2]
    print("cutout shape",cutout.shape)
    print("model shape:", model_hdu[0].data.shape)

    sky_value = float(model_hdu[0].header['2_SKY'].split("[")[1].split("]")[0])
    print("Sky-value in raw data was %.4f" % (sky_value))

    model_bgsub = model_data - numpy.min(model_data)
    model_peak = numpy.max(model_bgsub)

    min_flux = numpy.percentile(model_bgsub, 60)
    max_flux = numpy.percentile(model_bgsub, 65)
    print(min_flux, max_flux)

    #model_outskirts = (model_data > 0.05*model_peak) & (model_data < 0.1 * model_peak)
    model_outskirts = (model_bgsub > min_flux) & (model_bgsub < max_flux)


    ratio = (cutout - sky_value) / (model_data - sky_value)
    renomalize_factor = numpy.nanmedian((cutout-sky_value)[model_outskirts]) / \
                        numpy.nanmedian((model_bgsub)[model_outskirts])
    print(renomalize_factor)

    ratio /= renomalize_factor

    opt_depth = numpy.log(ratio)

    diff = (cutout - sky_value) - (model_data - sky_value)

    output_hdu = fits.HDUList([
        fits.PrimaryHDU(),
        fits.ImageHDU(data=cutout, name="DATA"),
        fits.ImageHDU(data=model_data, name="MODEL"),
        fits.ImageHDU(data=ratio, name="RATIO"),
        fits.ImageHDU(data=opt_depth, name="OPTDEPTH"),
        fits.ImageHDU(data=diff, name="DIFFERENCE"),
        fits.ImageHDU(data=model_outskirts.astype(numpy.int), name="OUTSKIRTS"),

    ])
    output_hdu.writeto(output_fn, overwrite=True)

    # fits.PrimaryHDU(data=cutout).writeto("cutout.fits", overwrite=True)

