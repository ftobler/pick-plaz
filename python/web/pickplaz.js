


function start() {
    app = new Vue({
        el: "#app",
        data: {
            nav: {
                page: 2
            },
            db: {

            },
            canvas: {
                ctx: null,
                cursor_px: { x: 0, y: 0 },
                cursor_mm: { x: 0, y: 0 },
                drag_start_mm: { x: 0, y: 0},
                drag: false,
                pos_mm: { x: 200, y: 200 },
                size: { x: 0, y: 0 },
                zoom: 1.2,
            }
        },
        mounted() {
            document.addEventListener('mousemove', this.mousemove)   
        },
        created() {
            this.poll()
            var c = document.getElementById("canvas-view");
            c.onmousewheel = this.mousewheel()
            this.ctx = c.getContext('2d');
        },
        methods: {
            poll() {
                ajax({
                    type: "GET",
                    dataType: "application/json",
                    url: "/api/data.json",
                    success: (data) => {
                        this.db = JSON.parse(data)
                        let i = 0
                        this.draw_stuff()
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
            },
            px_to_mm(px) {
                return this.px_to_mm_save(this.canvas.pos_mm, px)
            },
            px_to_mm_save(pos_mm, px) {
                return {
                    x: pos_mm.x + ((px.x - this.canvas.size.x/2) / this.canvas.zoom),
                    y: pos_mm.y + ((px.y - this.canvas.size.y/2) / this.canvas.zoom)
                }
            },
            show_coordinates(e) {
                this.canvas.cursor_px.x = e.offsetX;
                this.canvas.cursor_px.y = e.offsetY;
                let mm = this.px_to_mm(this.canvas.cursor_px)
                this.canvas.cursor_mm.x = Math.round(mm.x)
                this.canvas.cursor_mm.y = Math.round(mm.y)
            },
            draw_stuff() {
                var c = document.getElementById("canvas-view");
                this.canvas.size.x = c.width
                this.canvas.size.y = c.height
                if (c == null) {
                    return
                }
                let ctx = c.getContext('2d');
                ctx.lineWidth = 1 / this.canvas.zoom
                ctx.resetTransform()
                ctx.clearRect(0,0, c.width, c.height)
                ctx.translate(c.width / 2, c.height / 2)
                ctx.scale(this.canvas.zoom, this.canvas.zoom)
                ctx.translate(-this.canvas.pos_mm.x, -this.canvas.pos_mm.y)
                ctx.strokeStyle = "white"
                ctx.beginPath(); ctx.rect(0, 0, 400, 400); ctx.stroke();
                ctx.scale(1, 1)
            },
            mousewheel(e) {
                let fact = 1.1;
                if (event.wheelDelta < 0) {
                    fact = 1/fact;
                }
                this.canvas.zoom *= fact
                this.draw_stuff()
            },
            mousedown(event) {
                let canvas = document.getElementById("canvas-view");
                this.canvas.drag = true
                //this.canvas.drag_start_mm.x = this.canvas.pos_mm.x;
                //this.canvas.drag_start_mm.y = this.canvas.pos_mm.y;
                this.canvas.drag_start_mm = this.px_to_mm({
                    x: event.pageX - canvas.offsetLeft,
                    y: event.pageY - canvas.offsetTop
                })
            },
            mouseup(event) {
                this.canvas.drag = false
            },
            mousemove(event) {
                if (this.canvas.drag == true) {
                    let canvas = document.getElementById("canvas-view");
                    let dragEnd_mmm = this.px_to_mm_save(this.canvas.drag_start_mm, {
                        x: event.pageX - canvas.offsetLeft,
                        y: event.pageY - canvas.offsetTop
                    })
                    this.canvas.dragEnd_mmm = dragEnd_mmm
                    this.canvas.pos_mm.x = 2*this.canvas.drag_start_mm.x - dragEnd_mmm.x
                    this.canvas.pos_mm.y = 2*this.canvas.drag_start_mm.y - dragEnd_mmm.y
                    this.draw_stuff()
                }
            },
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