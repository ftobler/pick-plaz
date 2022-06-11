
const NAVPAGE = 2

function start() {
    initFootprints()
    app = new Vue({
        el: "#app",
        data: {
            page: NAVPAGE,
            dialogs: [],
            last_put_alert: -1,
            menu_hamburger: false,
            nav: {
            },
            debug: {
            },
            nav_init: false,
            context: {
                bom: [],
                feeder: {}
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
                zoom: 7
            },
            elements: {
                show_camera: true,
                center_camera: true,
                show_components: true,
                show_symbol: true,
                show_parts: true,
            },
            fiducial_bom: {}
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
            document.getElementById("app").style.visibility = "visible"
        },
        methods: {
            poll_data() {
                api.data((data) => {
                    this.context = JSON.parse(data)
                    let index = 0
                    for (let bom of this.context.bom) {
                        if (bom.fiducial == true) {
                            this.context.fiducial = index
                            this.fiducial_bom = bom;
                            break;
                        }
                        index++
                    }
                })
            },
            poll_image() {
                api.nav((data) => {
                    try {
                        this.nav = JSON.parse(data)
                        this.nav_init = true
                    } catch (e) {
                        console.log("Failed to load nav.json. More related errors might follow.")
                        throw e;
                    }

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

                    if (this.nav.alert != undefined && this.nav.alert != null) {
                        if (this.last_put_alert < this.nav.alert.id) {
                            if (this.activealert && this.activealert.id != this.nav.alert.id) {
                                console.log(JSON.stringify(this.nav.alert, null, 4))
                            }
                            let icon = "notifications"
                            let msg = this.nav.alert.msg.toLowerCase()
                            if (msg.includes("warn")) {
                                icon = "warning"
                            }
                            if (msg.includes("error") || msg.includes("exception") || msg.includes("fail")) {
                                icon = "error"
                            }
                            if (msg.includes("attention") || msg.includes("feedback")) {
                                icon = "feedback"
                            }
                            if (msg.includes("info")) {
                                icon = "info"
                            }
                            if (msg.includes("complete") || msg.includes("finish") || msg.includes("success") || msg.includes("done")) {
                                icon = "done"
                            }
                            this.show_dialog({
                                title: "Server Alert",
                                msg: this.nav.alert.msg,
                                answers: this.nav.alert.answers,
                                id: this.nav.alert.id,
                                material_image: icon,
                                callback: (data, answer) => {
                                    api.alert_quit(data.id, answer)
                                }
                            })
                            this.last_put_alert = this.nav.alert.id
                        }
                    } else {
                        this.activealert = null
                    }
                })
            },
            poll_debug() {
                api.debug((data) => {
                    this.debug = JSON.parse(data)
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
                this.show_coordinates(event)
            },
            show_coordinates(e) {
                this.canvas.cursor_px.x = e.offsetX;
                this.canvas.cursor_px.y = e.offsetY;
                let mm = this.px_to_mm(this.canvas.cursor_px)
                this.canvas.cursor_mm.x = mm.x
                this.canvas.cursor_mm.y = mm.y
            },
            keylistener(event) {
                if (this.dialogs.length > 0) {
                    return;
                }
                if (this.page == NAVPAGE) {
                    const stepwidth = 10 // mm
                    if (event.code == 'KeyW') {
                        this.do_key_move(0, -stepwidth)
                    } else if (event.code == 'KeyA') {
                        this.do_key_move(-stepwidth, 0)
                    } else if (event.code == 'KeyS') {
                        this.do_key_move(0, stepwidth)
                    } else if (event.code == 'KeyD') {
                        this.do_key_move(stepwidth, 0)
                    }
                }
            },
            do_nav(target_page) {
                this.page = target_page
                this.poll_data();
            },
            do_key_move(x, y) {
                this.canvas.pos_mm.x += x
                this.canvas.pos_mm.y += y
                this.do_setpos(this.nav.camera.x + x, this.nav.camera.y + y)
                this.draw_stuff()
            },
            do_setpos(x, y, system) {
                this.nav.camera.x = x
                this.nav.camera.y = y
                api.robot_setpos(this.nav.camera.x, this.nav.camera.y, system)
            },
            fiducial_assing_current_location(id, mode) {
                api.fiducial_assing_current_location(this.nav.detection.fiducial[0], this.nav.detection.fiducial[1], id, mode)
            },
            fiducial_reset() {
                api.fiducial_assing_current_location(0, 0, 0, "reset")
            },
            do_part_goto(part) {
                if (part.x == undefined || part.y == undefined) {
                    this.show_dialog({
                        title: "Error",
                        msg: "The part part does not have XY coordinates to drive to.",
                        material_image: "error",
                    })
                    return;
                }
                this.do_setpos(part.x, part.y, "pcb")
            },
            do_part_place(designator) {
                api.sequence("place_part", designator)
            },
            do_sequence(method, param) {
                //param is optional
                api.sequence(method, param)
            },
            do_save_restore(method) {
                api.file_get_list((raw) => {
                    try {
                        file_list = JSON.parse(raw).files;
                        if (method == "save") {
                            this.show_dialog({
                                title: "Save",
                                msg: "Enter a filename to save the current context to.",
                                answers: ["OK", "Cancel"],
                                input: true,
                                dropdown: file_list,
                                material_image: "save",
                                callback: (data, answer) => {
                                    if (answer == "OK") {
                                        api.file_context_save(data.input_data, () => {
                                            this.poll_data()
                                        })
                                    }
                                }
                            })
                        } else if (method == "restore") {
                            this.show_dialog({
                                title: "Restore",
                                msg: "Enter the filename of the context to load.",
                                answers: ["OK", "Cancel"],
                                input: true,
                                dropdown: file_list,
                                material_image: "restore",
                                callback: (data, answer) => {
                                    if (answer == "OK") {
                                        api.file_context_read(data.input_data, () => {
                                            this.poll_data()
                                        })
                                    }
                                }
                            })
                        }
                    } catch (e) {
                        api_exception("file_get_list failed");
                        throw e;
                    }
                })
            },


            do_modify_bom_doplace(bom, i) {
                api.bom_modify("place", i, bom.place, () => {
                    this.poll_data()
                })
            },
            do_modify_bom_isfiducial(bom, i) {
                api.bom_modify("fiducial", i, bom.fiducial, () => {
                    this.poll_data()
                })
            },
            do_modify_bom_footprint(bom, i) {
                let footprint_names = []
                for (const [name, feeder] of Object.entries(footprints)) {
                    footprint_names.push(name)
                }
                if (footprint_names.length == 0) {
                    return
                }
                this.show_dialog({
                    title: "Edit BOM",
                    msg: "Select a new Footprint name",
                    dropdown: footprint_names,
                    answers: ["OK", "Cancel"],
                    material_image: "edit",
                    callback: (data, answer) => {
                        if (answer == "OK") {
                            api.bom_modify("footprint", i, data.input_data, () => {
                                this.poll_data()
                            })
                        }
                    }
                })
            },
            do_modify_bom_feeder(bom, i) {
                let feeder_names = []
                for (const [name, feeder] of Object.entries(this.context.feeder)) {
                    feeder_names.push(name)
                }
                if (feeder_names.length == 0) {
                    return
                }
                this.show_dialog({
                    title: "Edit BOM",
                    msg: "Select a new Feeder name.",
                    answers: feeder_names,
                    material_image: "edit",
                    callback: (data, answer) => {
                        if (answer != null) {
                            api.bom_modify("feeder", i, answer, () => {
                                this.poll_data()
                            })
                        }
                    }
                })
            },
            do_modify_bom_rotation(bom, i) {
                api.bom_modify("rotation", i, null, () => {
                    this.poll_data()
                })
            },
            do_modify_part_state(id) {
                api.part_modify("state", id, null, () => {
                    this.poll_data()
                })
            },

            do_modify_feeder_rotation(feeder) {
                api.feeder_modify("rotation", feeder, null, () => {
                    this.poll_data()
                })
            },
            do_modify_feeder_state(feeder) {
                api.feeder_modify("state", feeder, null, () => {
                    this.poll_data()
                })
            },
            do_modify_feeder_attribute(feeder, feeder_obj, attribute) {
                this.show_dialog({
                    title: "Edit Feeder",
                    msg: "Enter a new numerical value for '" + attribute + "'.",
                    input: true,
                    input_data: feeder_obj[attribute],
                    answers: ["OK", "Cancel"],
                    material_image: "edit",
                    callback: (data, answer) => {
                        if (answer == "OK") {
                            api.feeder_modify(attribute, feeder, data.input_data, () => {
                                this.poll_data()
                            })
                        }
                    }
                })
            },

            do_feeder_goto(feeder) {
                api.feeder_action(feeder, "goto", () => {
                    this.poll_data()
                })
            },
            do_feeder_test(feeder) {
                api.feeder_action(feeder, "test", () => {
                    this.poll_data()
                })
            },



            do_upload() {
                let form = document.getElementById("upload_form");
                //form.submit();
                api.do_upload(form, (err) => {
                    let msg
                    let image
                    if (err.error != undefined) {
                        msg = "Upload Failed. " + err.error
                        image = "error"
                    } else {
                        msg = "Upload Success."
                        image = "done"
                    }
                    this.show_dialog({
                        title: "Upload",
                        msg: msg,
                        material_image: image
                    })
                })
            },
            show_dialog(config) {
                //let data = {
                //    title: "title",
                //    msg: "message",
                //    input: false,
                //    dropdown: ["sel1"],
                //    selection: ["sel1"],
                //    answers: ["OK"],
                //    id: 0,
                //    material_image: "info",
                //    callback: (data, answer) => {}
                //}
                if (config.answers == undefined || config.answers == null || config.answers.length == 0) {
                    config.answers = ["OK"]
                }
                if (config.selection == undefined) {
                    config.selection = []
                }
                if (config.input == undefined) {
                    config.input = false
                }
                if (config.unit == undefined) {
                    config.unit = ""
                }
                if (config.material_image == undefined) {
                    config.material_image = "notifications"
                }
                if (config.dropdown) {
                    config.input = true
                }
                if (config.close == undefined) {
                    config.close = true
                }
                if (config.dropdown && config.input_data == undefined) {
                    if (config.dropdown.length > 0) {
                        config.input_data = config.dropdown[0]
                    } else {
                        config.input_data = ""
                    }
                }
                this.dialogs.push(config)
            },
            do_dialog_quit(answer) {
                console.log("do_dialog_quit");
                let config = this.dialogs[0]
                if (config.callback != undefined) {
                    config.callback(config, answer);
                }
                this.dialogs.shift()  //remove first element
            },
            dialog_user_confirm(message, success_callback) {
                this.show_dialog({
                    title: "Confirm",
                    msg: message,
                    answers: ["Yes", "No"],
                    callback: (config, answer) => {
                        if (answer == "Yes") {
                            success_callback()
                        }
                    }
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
                ctx.font = "2px Arial";
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

                //draw camera group
                if (this.elements.show_camera) {
                    //draw topdn image
                    this.draw_camera(ctx, this.image.topdn, this.nav.camera)

                    //draw camera position
                    ctx.save();
                    ctx.globalAlpha = 0.5;
                    ctx.strokeStyle = "yellow";
                    ctx.beginPath();
                    ctx.moveTo(this.nav.camera.x, this.nav.bed[0]-10);
                    ctx.lineTo(this.nav.camera.x, this.nav.bed[0]+this.nav.bed[2]+10);
                    ctx.moveTo(this.nav.bed[1]-10, this.nav.camera.y);
                    ctx.lineTo(this.nav.bed[1]+this.nav.bed[3]+10, this.nav.camera.y);
                    ctx.stroke();
                    ctx.restore();
                }

                //draw bed outline
                ctx.strokeStyle = "white"
                ctx.beginPath(); ctx.rect(this.nav.bed[0], this.nav.bed[1], this.nav.bed[2], this.nav.bed[3]); ctx.stroke();
                ctx.scale(1, 1)

                //draw other bed shape stuff
                ctx.strokeStyle = "gray"
                for (let shape of this.nav.bed_shapes) {
                    ctx.beginPath(); ctx.rect(shape[0], shape[1], shape[2], shape[3]);
                    ctx.stroke();
                }
                ctx.scale(1, 1)

                //draw detected fiducial
                if (this.elements.show_symbol) {
                    ctx.strokeStyle = "yellow"
                    this.draw_fiducial(ctx, this.nav.detection.fiducial, "detection")

                    this.draw_detection(ctx, this.nav.detection.part, "part")
                    //draw detected fiducials
                    if (this.elements.show_symbol) {
                        ctx.strokeStyle = "yellow"
                        for (let [id, coord] of Object.entries(this.nav.pcb.fiducials)) {
                            this.draw_fiducial(ctx, coord, id)
                        }
                    }
                }

                //draw pcb
                ctx.save()
                let t = this.nav.pcb.transform
                ctx.transform(t[0], t[1], t[2], t[3], t[4], t[5])
                //draw pcb origin
                if (this.elements.show_symbol) {
                    ctx.strokeStyle = "white"
                    ctx.fillStyle = "white"
                    ctx.beginPath();
                    ctx.moveTo(0, +10)
                    ctx.lineTo(0, 0)
                    ctx.lineTo(10, 0)
                    ctx.moveTo(-1, +8)
                    ctx.lineTo(0, +10)
                    ctx.lineTo(1, +8)
                    ctx.moveTo(8, -1)
                    ctx.lineTo(10, 0)
                    ctx.lineTo(8, 1)
                    ctx.stroke()
                    ctx.beginPath();
                    ctx.arc(0, 0, 1, 0, 2 * Math.PI)
                    ctx.stroke()

                    ctx.save()
                    // text is drawn in cairo coordinates
                    ctx.transform(1, 0, 0, -1, 0, 0)
                    ctx.fillText("x", 10.2, 0.2);
                    ctx.fillText("y", 0.2, -10.2);
                    ctx.restore()
                }
                //draw the parts
                for (let entry of this.context.bom) {
                    if (entry.place == true || entry.fiducial == true) {
                        for (let [id, part] of Object.entries(entry.designators)) {
                            let deg = 0
                            if (entry.rot != undefined) deg += entry.rot
                            if (part.rot != undefined) deg += part.rot
                            let rad = deg * Math.PI / 180

                            ctx.save()
                            ctx.translate(part.x, part.y)
                            ctx.rotate(rad)
                            // PCB has coordinate origin bottom left
                            // this must be corrected here
                            ctx.transform(1, 0, 0, -1, 0, 0)

                            this.drawSymbol(ctx, entry, id)

                            ctx.restore()
                        }
                    }
                }
                ctx.restore();

                //draw feeder
                for (const [name, feeder] of Object.entries(this.context.feeder)) {
                    try {
                        let part = undefined
                        for (let entry of this.context.bom) {
                            if (entry.feeder == name) {
                                part = entry
                            }
                        }

                        if (feeder.type == 0)
                            this.draw_tray_feeder(ctx, name, feeder, part)
                        if (feeder.type == 1)
                            this.draw_belt_feeder(ctx, name, feeder, part)
                    } catch (e) {
                        console.log(e)
                    }
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
            },
            draw_fiducial(ctx, coord, text) {
                ctx.beginPath();
                ctx.arc(coord[0], coord[1], 0.75, 0, 2 * Math.PI)
                ctx.stroke();
                ctx.beginPath();
                ctx.arc(coord[0], coord[1], 1.5, 0, 2 * Math.PI)
                ctx.stroke();
                ctx.fillText(text, coord[0] + 0.2, coord[1] - 0.2);
            },
            draw_detection(ctx, coord, text) {
                ctx.save();
                ctx.translate(coord[0], coord[1]);

                ctx.beginPath();
                ctx.arc(0, 0, 0.75, 0, 2 * Math.PI);
                ctx.stroke();
                ctx.beginPath();
                ctx.arc(0, 0, 1.5, 0, 2 * Math.PI);
                ctx.stroke();
                ctx.fillText(text, 0.2, 0.2);

                ctx.rotate(-coord[2]);
                ctx.moveTo(-2,0);
                ctx.lineTo(2,0);
                ctx.stroke();
                ctx.moveTo(0,-3);
                ctx.lineTo(0,3);
                ctx.stroke();

                ctx.restore();
            },
            drawSymbol(ctx, entry, id) {

                const crossSize = 1.0
                const textSize = 0.5

                ctx.strokeStyle = "red"
                ctx.fillStyle = "red"

                let footprint = getFootprint(entry.footprint)

                if (footprint && this.elements.show_parts) {

                    ctx.save()
                    ctx.globalAlpha = 0.8
                    this.draw_part(ctx, footprint)
                    ctx.restore()
                }

                if (this.elements.show_symbol) {

                    ctx.save()
                    ctx.transform(crossSize, 0, 0, crossSize, 0, 0)

                    this.draw_part_cross(ctx)

                    if (entry.fiducial == true) {
                        ctx.strokeStyle = "white"
                        ctx.beginPath();
                        ctx.arc(0, 0, 1, 0, 2 * Math.PI)
                        ctx.stroke()
                    }

                    ctx.restore()

                    if (id !== undefined) {
                        ctx.save()
                        ctx.transform(textSize, 0, 0, textSize, 0, 0)
                        ctx.fillText(id, 0.2, -0.2);
                        ctx.restore()
                    }
                }
            },
            draw_tray_feeder(ctx, name, feeder, part) {

                let d = 2; // margin

                ctx.save();
                ctx.translate(feeder.position[0], feeder.position[1]);

                ctx.fillStyle = "cyan"
                ctx.strokeStyle = "cyan"

                ctx.moveTo(0,feeder.position[3]);

                textLines = [name]

                if (part) {

                    textLines.push(part.partnr)

                    let footprint = getFootprint(part.footprint)
                    if (footprint) {
                        // scale sym size into a 10x10mm box
                        let factor = Math.max(footprint.imageSym.height, footprint.imageSym.width) / 10
                        let h = footprint.imageSym.height / factor;
                        let w = footprint.imageSym.width / factor;

                        ctx.save();
                        ctx.translate(feeder.position[2] / 3, feeder.position[3] / 2);
                        ctx.rotate(feeder.rot*Math.PI/180)
                        try {
                            ctx.drawImage(
                                footprint.imageSym,
                                -w / 2,
                                -h / 2,
                                w,
                                h
                            );
                        } catch {}
                        ctx.restore()

                        ctx.save();
                        ctx.translate(feeder.position[2] / 3 * 2, feeder.position[3] / 2);
                        ctx.rotate(feeder.rot*Math.PI/180)
                        this.draw_part(ctx, footprint)
                        this.draw_part_cross(ctx)
                        ctx.restore()

                    } else {
                        let txt = "no part symbol"
                        let metrics = ctx.measureText(txt);
                        ctx.fillText(
                            txt,
                            feeder.position[2] / 2 - metrics.position[2]/2,
                            feeder.position[3] / 2
                        );

                    }

                }

                let metrics = ctx.measureText("");
                let fontHeight = metrics.fontBoundingBoxAscent + metrics.fontBoundingBoxDescent;
                let y = fontHeight;
                for (let line of textLines) {
                    ctx.fillText(line, d+1, d+y);
                    y += fontHeight;
                }

                ctx.save();
                ctx.font = "5px Arial";
                let txt = this.context.const.feeder_state[feeder.state]

                if (feeder.state == 1) {ctx.fillStyle = "green"; ctx.strokeStyle = "green"}
                if (feeder.state == 2) {ctx.fillStyle = "red"; ctx.strokeStyle = "red"}

                metrics = ctx.measureText(txt);
                ctx.fillText(
                    txt,
                    feeder.position[2] / 2 - metrics.width /2,
                    feeder.position[3] - 3 - d
                );

                if (feeder.state != 0) {
                    ctx.beginPath();
                    ctx.lineWidth = d;
                    ctx.globalAlpha = 0.5
                    ctx.rect(d/2, d/2, feeder.position[2] - d, feeder.position[3] - d);
                    ctx.stroke();
                }
                ctx.restore();

                ctx.beginPath();
                ctx.rect(0, 0, feeder.position[2], feeder.position[3]);
                ctx.stroke();

                ctx.restore();
            },
            draw_belt_feeder(ctx, name, feeder, part) {
                let d = 2; // margin

                //draw the crosses (main positions)
                ctx.strokeStyle = "red"
                this.draw_cross(ctx, feeder.start[0], feeder.start[1])
                this.draw_cross(ctx, feeder.current[0], feeder.current[1])
                this.draw_cross(ctx, feeder.current[0] + feeder.offset[0], feeder.current[1] + feeder.offset[1])
                this.draw_cross(ctx, feeder.end[0], feeder.end[1])

                ctx.fillStyle = "cyan"
                ctx.strokeStyle = "cyan"
                ctx.save();
                ctx.translate(feeder.x + feeder.x_offset, feeder.y + feeder.y_offset)
                ctx.rotate(feeder.rot*Math.PI/180)
                try {
                    let footprint = getFootprint(part.footprint)
                    this.draw_part(ctx, footprint)
                    this.draw_part_cross(ctx)
                } catch {}

                ctx.fillText(name, feeder.position[0] + 2.5, feeder.position[1] + 4);

                ctx.restore();

                ctx.save();
                ctx.translate(feeder.position[0], feeder.position[1])

                ctx.save();
                ctx.font = "5px Arial";
                let txt = this.context.const.feeder_state[feeder.state]

                if (feeder.state == 1) {ctx.fillStyle = "green"; ctx.strokeStyle = "green"}
                if (feeder.state == 2) {ctx.fillStyle = "red"; ctx.strokeStyle = "red"}

                metrics = ctx.measureText(txt);
                ctx.fillText(
                    txt,
                    feeder.position[2] / 2 - metrics.width /2,
                    feeder.position[3] - 3 - d
                );

                if (feeder.state != 0) {
                    ctx.beginPath();
                    ctx.lineWidth = d;
                    ctx.globalAlpha = 0.5
                    ctx.rect(d/2, d/2, feeder.position[2] - d, feeder.position[3] - d);
                    ctx.stroke();
                }
                ctx.restore();

                ctx.beginPath();
                ctx.rect(0, 0, feeder.position[2], feeder.position[3]);
                ctx.stroke();
                ctx.restore();

            },
            draw_cross(ctx, x, y) {
                ctx.save();
                ctx.translate(x, y);
                ctx.beginPath();
                ctx.moveTo(0,-1)
                ctx.lineTo(0, 1)
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(-1,0)
                ctx.lineTo( 1,0)
                ctx.stroke();
                ctx.restore()
            },
            draw_part(ctx, footprint) {
                try {
                    ctx.drawImage(
                        footprint.imageImg,
                        -footprint.x / 2,
                        -footprint.y / 2,
                        footprint.x,
                        footprint.y
                    );
                    //draw the footprint name
                    ctx.save()
                    ctx.fillStyle = "#00000080"
                    ctx.textAlign = "center";
                    const textSize = 0.5
                    ctx.transform(textSize/3, 0, 0, textSize/3, 0, 0)
                    ctx.fillText(footprint.name, 0.0, 0.7);
                    ctx.restore()
                } catch {
                    console.log("drawing error for part symbol")
                }
            },
            draw_part_cross(ctx) {
                ctx.strokeStyle = "red"
                ctx.fillStyle = "red"

                //first cross line
                ctx.beginPath();
                ctx.moveTo(0,-1)
                ctx.lineTo(0, 1)
                ctx.stroke();

                //second cross line
                ctx.beginPath();
                ctx.moveTo(-1,0)
                ctx.lineTo(1, 0)
                ctx.stroke();

                //arrow head
                ctx.beginPath();
                ctx.moveTo(0, -1)
                ctx.lineTo(-0.1, -0.75)
                ctx.lineTo(0, -0.8) // <- make them more fancy
                ctx.lineTo(0.1, -0.75)
                ctx.lineTo(0, -1)
                ctx.fill();
            },
            part_state: function(i) {
                return this.context.const.part_state[i]
            },
            feeder_state: function(i) {
                return this.context.const.feeder_state[i]
            },
            feeder_type: function(i) {
                return this.context.const.feeder_type[i]
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
            round: function(v) {
                return Math.round(v*100)/100
            },
        }

    })
}


api = {
    data(cb) {
        apicall("context.json", {}, cb, false)
    },
    nav(cb) {
        apicall("nav.json", {}, cb, false)
    },
    debug(cb) {
        apicall("debug", {}, cb, true)
    },
    fiducial_assing_current_location(x_global, y_global, id, method) {
        let methods = ["assign", "unassign", "reset"]
        if (methods.includes(method)) {
            apicall("setfiducial", {
                x: x_global,
                y: y_global,
                id: id,
                method: method
            })
        } else {
            api_exception("fiducial_assing_current_location rejected the request client side '" + method + "'");
        }
    },
    robot_setpos(x_global, y_global, system) {
        if (system == undefined) {
            system = "global"
        }
        apicall("setpos", {
            x: x_global,
            y: y_global,
            system: system
        })
    },
    sequence(method, param) {
        apicall("sequencecontrol", {
            method: method,
            param: param
        })
    },
    feeder_action(feeder, action) { //TODO: python implemenation
        let methods = ["goto", "test"]
        if (methods.includes(action)) {
            apicall("feeder_action", {
                feeder: feeder,
                action: action
            })
        } else {
            api_exception("feeder_action rejected the request client side '" + action + "'");
        }
    },
    alert_quit(id, answer) {
        apicall("alertquit", {
            id: id,
            answer: answer
        })
    },

    //file handling
    do_upload(form, event) {
        var form_data = new FormData(form);
        console.log("api 'upload'")
        fetch('/api/upload', {method: "POST", body: form_data}).then(response => response.json()).then((json) => {
            if (event != undefined) {
                event(json)
            }
        })
    },
    file_get_list(callback) { //TODO: python implemenation
        apicall("file_context", {
            method: "list"
        }, callback)
    },
    file_context_save(filename, callback) { //TODO: python implemenation
        apicall("file_context", {
            method: "save",
            filename: filename
        }, callback)
    },
    file_context_read(filename, callback) { //TODO: python implemenation
        apicall("file_context", {
            method: "read",
            filename: filename
        }, callback)
    },

    // bom/part/feeder handling
    bom_modify(method, index, data, callback) { //TODO: python implemenation
        let methods = ["place", "fiducial", "footprint", "feeder", "rotation"]
        if (methods.includes(method)) {
            apicall("bom_modify", {
                method: method,
                index: index,
                data: data
            }, callback)
        } else {
            api_exception("bom_modify rejected the request client side '" + method + "'");
        }
    },
    part_modify(method, id, data, callback) { //TODO: python implemenation
        let methods = ["state"]
        if (methods.includes(method)) {
            apicall("part_modify", {
                method: method,
                id: id,
                data: data,
            }, callback)
        } else {
            api_exception("part_modify rejected the request client side '" + method + "'");
        }
    },
    feeder_modify(method, feeder, data, callback) { //TODO: python implemenation
        let methods = ["rename", "type", "rotation", "state", "delete", "create", "x", "y", "width", "height", "pitch", "x_offset", "y_offset"]
        if (methods.includes(method)) {
            apicall("feeder_modify", {
                method: method,
                feeder: feeder,
                data: data,
            }, callback)
        } else {
            api_exception("feeder_modify rejected the request client side '" + method + "'");
        }
    },

}

function apicall(scope, arguments, cb, debug_print) {
    if (debug_print != false) {
        console.log("api '" + scope + "' " + JSON.stringify(arguments))
    }
    ajax({
        type: "POST",
        dataType: "application/json",
        url: "/api/" + scope + build_query_parameter(arguments),
        success: cb,
        error: (data) => {
            api_exception("Apicall to '" + scope + "' failed.");
        }
    })
}

function api_exception(msg) {
    app.show_dialog({
        title: "API Exception",
        msg: msg,
        material_image: "new_releases", //nearby_error
        answers: ["Ouch!"]
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



