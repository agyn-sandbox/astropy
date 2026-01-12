Fix SlicedLowLevelWCS.world_to_pixel_values for sliced correlated WCS (PC mixing): fill dropped world axes with the world values implied by the fixed pixel slice instead of a constant. This corrects large errors in pixel coordinates after slicing.

