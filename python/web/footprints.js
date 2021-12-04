footprints = {}

function initFootprints() {
    ajax({
	    type: "GET",
	    url: "/footprints.json",
		success: (data) => {
            footprints = JSON.parse(data)
	    },
	    dataType: "application/json"
	})
}

function getFootprint(footprint_name) {
    footprint = footprints[footprint_name]
    if (footprint !== undefined) {
        if (footprint.imageImg === undefined) {
            footprint.imageImg = new Image(footprint.x, footprint.y);
            footprint.imageImg.src = "parts/" + footprint.img
            footprint.imageSym = new Image();
            footprint.imageSym.src = "parts/" + footprint.sym
            footprint.name = footprint_name.replace("_img.svg", "")
        }
    }
    return footprint
}
