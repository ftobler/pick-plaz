


function start() {
    app = new Vue({
        el: "#app",
        data: {
            nav: {
                page: 0
            },
            db: {

            }
        },
        created() {
            this.poll()
        },
        methods: {
            poll: function() {
                ajax({
                    type: "GET",
                    dataType: "application/json",
                    url: "/api/data.json",
                    success: (data) => {
                        this.db = JSON.parse(data)
                        let i = 0
                        /**for (const bom of this.db.bom) {
                            console.log(bom)
                            for (const id of bom.id) {
                                console.log(id)
                                let part = this.db.parts[id]
                                if (part != undefined) {
                                    part._bom = i
                                    part._footprint = bom.footprint
                                    part._place = bom.place
                                    part._fiducal = bom.fiducal
                                }
                            }
                            i++
                        }*/
                    },
                })
            }
        },
        filters: {
            footprint_img_path: function(f) {
                let dat = footprints[f]
                if (dat) {
                    return "/parts/" + dat.img
                }
                return ""
            },
            footprint_sym_path: function(f) {
                let dat = footprints[f]
                if (dat) {
                    return "/parts/" + dat.sym
                }
                return ""
            },
        }

    })
}


/*
ajax({
	    type: "GET",
	    url: "/something",
		success: (data) => {                        
	    },
	    dataType: "application/json"
	})
*/
function ajax(setting) {
	if (typeof(shutdown) !== 'undefined') return
	var request = new XMLHttpRequest();
	request.open(setting.type, setting.url, true);
	request.setRequestHeader('Content-Type', setting.dataType)
	request.onload = function(data) {
		if (typeof(shutdown) !== 'undefined') return
		if (this.status >= 200 && this.status < 400) {
			if (setting.success) {
				setting.success(this.response)
			}
		} else {
			if (setting.error) {
				setting.error(this.response)
			}
		}
	}
	request.onerror = function(data) {
		if (typeof(shutdown) !== 'undefined') return
		if (setting.error) {
			setting.error(data)
		}
	}
	if (setting.data) {
		request.send(setting.data)
	} else {
		request.send()
	}
}


function build_query_parameter(obj) {
    let esc = encodeURIComponent;
    if (Object.keys(obj).length == 0) {
        return ""
    }
    return "?" + Object.keys(obj)
        .map(k => esc(k) + '=' + esc(obj[k]))
        .join('&');
}


function pad(num, size) {
    num = num.toString();
    while (num.length < size) num = "0" + num;
    return num;
}