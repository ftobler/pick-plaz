
const NAVPAGE = 2

function start() {
    app = new Vue({
        el: "#app",
        data: {
            page: NAVPAGE,
            nav: {
            },
            nav_init: false,
            db: {
            },
            image: {
                botup : null,
                botup_nr : 0,
                topdn : null,
                topdn_nr : 0,
            },
            canvas: {
                ctx: null,
                cursor_px: { x: 0, y: 0 },
                cursor_mm: { x: 0, y: 0 },
                drag_start_mm: { x: 0, y: 0},
                drag: false,
                pos_mm: { x: 200, y: 200 },
                size: { x: 0, y: 0 },
                zoom: 15,
            },
            elements: {
                show_camera: true,
                center_camera: true,
                show_components: true,
                show_symbol: true,
            }
        },
        mounted() {
            document.addEventListener('mousemove', this.mousemove)
            document.addEventListener('keyup', this.keylistener)
        },
        created() {
            this.poll_data()
            this.poll_image()
            var c = document.getElementById("canvas-view");
            c.onmousewheel = this.mousewheel()
            this.ctx = c.getContext('2d');
        },
        methods: {
            poll_data() {
                ajax({
                    type: "GET",
                    dataType: "application/json",
                    url: "/api/data.json",
                    success: (data) => {
                        this.db = JSON.parse(data)
                    },
                })
            },
            poll_image() {
                ajax({
                    type: "GET",
                    dataType: "application/json",
                    url: "/api/nav.json",
                    success: (data) => {
                        this.nav = JSON.parse(data)
                        this.nav_init = true

                        if (this.elements.show_camera && this.page==NAVPAGE) {
                            let temp_img = new Image(10,10);
                            temp_img.onload = () => {
                                this.image.topdn = temp_img
                                this.draw_stuff()
                                setTimeout(() => {
                                    this.poll_image()
                                }, 300)
                            }
                            temp_img.src = "/api/topdn.jpg?nr=" + this.nav.camera.framenr + "&t=" + Date.now()
                        } else {
                            this.image.topdn = null
                            setTimeout(() => {
                                this.poll_image()
                            }, 300)
                        }
                        this.draw_stuff()
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
            mousewheel(e) {
                let fact = 1.1;
                if (event.wheelDelta < 0) {
                    fact = 1/fact;
                }
                this.canvas.zoom *= fact
                this.draw_stuff()
            },
            mousedown(event) {
                if (event.button == 0) { //left button
                    
                } else if (event.button == 1) { //middle button
                    let canvas = document.getElementById("canvas-view");
                    this.canvas.drag = true
                    //this.canvas.drag_start_mm.x = this.canvas.pos_mm.x;
                    //this.canvas.drag_start_mm.y = this.canvas.pos_mm.y;
                    this.canvas.drag_start_mm = this.px_to_mm({
                        x: event.pageX - canvas.offsetLeft,
                        y: event.pageY - canvas.offsetTop
                    })
                } else if (event.button == 2) { //right button

                }
            },
            mouseup(event) {
                if (event.button == 0) { //left button
                    
                } else if (event.button == 1) { //middle button
                    this.canvas.drag = false
                } else if (event.button == 2) { //right button

                }
            },
            mouseclick(event) {
                if (event.button == 0) { //left button
                    this.do_setpos(this.canvas.cursor_mm.x, this.canvas.cursor_mm.y)
                } else if (event.button == 1) { //middle button

                } else if (event.button == 2) { //right button

                }
            },
            mousemove(event) {
                if (this.page == NAVPAGE) {
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
                }
            },
            keylistener(event) {
                if (this.page == NAVPAGE) {
                    const stepwidth = 10 // mm
                    if (event.code == 'KeyW') {
                        this.do_move(0, -stepwidth)
                    } else if (event.code == 'KeyA') {
                        this.do_move(-stepwidth, 0)
                    } else if (event.code == 'KeyS') {
                        this.do_move(0, stepwidth)
                    } else if (event.code == 'KeyD') {
                        this.do_move(stepwidth, 0)
                    }
                }
            },
            do_move(x, y) {
                this.canvas.pos_mm.x += x
                this.canvas.pos_mm.y += y
                this.do_setpos(this.nav.camera.x + x, this.nav.camera.y + y)
                this.draw_stuff()
            },
            do_setpos(x, y) {
                this.nav.camera.x = x
                this.nav.camera.y = y
                ajax({
                    type: "GET",
                    dataType: "application/json",
                    url: "/api/setpos?x=" + this.nav.camera.x + "&y=" + this.nav.camera.y,
                    success: (data) => {
                        
                    },
                })
            },
            draw_stuff() {
                var c = document.getElementById("canvas-view");
                if (c == null || this.nav_init == false) {
                    return
                }
                this.canvas.size.x = c.width
                this.canvas.size.y = c.height
                let ctx = c.getContext('2d');
                ctx.lineWidth = 1 / this.canvas.zoom
                ctx.resetTransform()
                ctx.clearRect(0,0, c.width, c.height)
                ctx.translate(c.width / 2 + 0.5, c.height / 2 + 0.5)
                ctx.scale(this.canvas.zoom, this.canvas.zoom)
                if (this.elements.center_camera) {
                    this.canvas.pos_mm.x = this.nav.camera.x
                    this.canvas.pos_mm.y = this.nav.camera.y
                }
                ctx.translate(-this.canvas.pos_mm.x, -this.canvas.pos_mm.y)


                //draw bed outline
                ctx.strokeStyle = "white"
                ctx.beginPath(); ctx.rect(this.nav.bed.x, this.nav.bed.y, this.nav.bed.width, this.nav.bed.height); ctx.stroke();
                ctx.scale(1, 1)

                
                if (this.elements.show_camera) {
                    //draw topdn image
                    this.draw_camera(ctx, this.image.topdn, this.nav.camera)

                    //draw camera position
                    ctx.strokeStyle = "yellow"
                    ctx.beginPath();
                    ctx.moveTo(this.nav.camera.x, this.nav.bed.x-10);
                    ctx.lineTo(this.nav.camera.x, this.nav.bed.x+this.nav.bed.width+10);
                    ctx.moveTo(this.nav.bed.y-10, this.nav.camera.y);
                    ctx.lineTo(this.nav.bed.y+this.nav.bed.height+10, this.nav.camera.y);
                    ctx.stroke();
                }

                


            },
            draw_camera(ctx, image, position) {
                if (image != null) {
                    ctx.drawImage(
                        image, 
                        position.x - position.width / 2, 
                        position.y - position.height / 2, 
                        position.width, 
                        position.height
                    );
                } else {
                    ctx.strokeStyle = "yellow"
                    ctx.beginPath(); ctx.rect(
                        position.x - position.width / 2, 
                        position.y - position.height / 2, 
                        position.width, 
                        position.height
                    ); ctx.stroke();
                }
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