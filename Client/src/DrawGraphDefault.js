var ClearGraph = function (dst) {
    var canvas = document.getElementById(dst);
    canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
};

var DrawGraphDefault = function (dst, grapharray, gridoffset, gtype
    , step, thick, griddensity
    , minval, maxval
    , autoscale
    , bo_100
    , showbg, bgcolor
    , showframe, framecolor
    , showgrid, gridcolor
    , graphcolor
    , showvalue
    , showscale, fontfamily, fontcolor, fontsize, fontstyle, fontvariant, fontweight, rightalign) {
    var canvas = document.getElementById(dst);
    var ctx = canvas.getContext("2d");
    var W = canvas.width;
    var H = canvas.height;
    var x1 = 0;
    var y1 = 0;
    var x2 = W - 1;
    var y2 = H - 1;
    var gtype_ag = (gtype == "AG");
    var gtype_hg = (gtype == "HG");
    ctx.clearRect(0, 0, W, H);
    if (showframe) {
        x1++;
        y1++;
        x2--;
        y2--;
        W = W - 2;
        H = H - 2;
    }
    var r_minval;
    var r_maxval;
    var i_graph_width_half = (W / 2) + 1;
    if (autoscale) {
        r_minval = +1e9;
        r_maxval = -1e9;
        var i_minval;
        var i_maxval;
        var value_x = x2;
        var bo_break = false;
        for (i = 0; i < i_graph_width_half; i++)
            if (i < grapharray.length) {
                if (grapharray[i] < r_minval)
                    r_minval = grapharray[i];
                if (grapharray[i] > r_maxval)
                    r_maxval = grapharray[i];
                if (bo_break)
                    break;
                if (gtype_hg) {
                    value_x -= (thick + step);
                    if (value_x < x1)
                        break;
                } else {
                    value_x -= (step + 1);
                    if (value_x < x1)
                        bo_break = true;
                }
            }
        if (r_minval == +1e9)
            r_minval = 0;
        if (r_maxval == -1e9)
            r_maxval = 0;
        if (bo_100) {
            i_minval = Math.round(r_minval * 0.009) * 100;
            i_maxval = Math.round(r_maxval * 0.011) * 100;
            if (i_minval > r_minval)
                i_minval = Math.floor(r_minval) * 100;
            while (i_maxval <= i_minval)
                i_maxval = i_maxval + 100;
        } else {
            i_minval = Math.round(r_minval * 0.9);
            i_maxval = Math.round(r_maxval * 1.1);
            if (i_minval > r_minval)
                i_minval = Math.floor(r_minval);
            if (i_maxval < r_maxval)
                i_maxval++;
            while (i_maxval <= i_minval)
                i_maxval += 2;
        }
        r_minval = i_minval;
        r_maxval = i_maxval;
    } else {
        r_minval = minval;
        r_maxval = maxval;
    }
    if (showbg) {
        ctx.fillStyle = bgcolor;
        ctx.fillRect(x1, y1, W, H);
    }
    if (showgrid) {
        ctx.fillStyle = gridcolor;
        if (!gtype_hg)
            for (i = 0; i < W; i++)
                if ((i % griddensity) == gridoffset)
                    ctx.fillRect(x1 + i, y1, 1, y2 - y1 + 1)
                    for (i = H - 1; i >= 0; i--)
                        if ((i % griddensity) == 0)
                            if ((!showframe) || (i))
                                ctx.fillRect(x1, y2 - i, x2 - x1 + 1, 1)
    }
    var val_range = r_maxval - r_minval;
    var value_x = x2;
    if (gtype_hg) {
        ctx.fillStyle = graphcolor;
        for (i = 0; i < i_graph_width_half; i++)
            if (i < grapharray.length) {
                var value_y = y2 - Math.floor((grapharray[i] - r_minval) / val_range * H);
                ctx.fillRect(value_x - (thick - 1), value_y, thick, y2 - value_y + 1);
                value_x -= (thick + step);
                if (value_x < x1)
                    break;
            }
    } else {
        var bo_first = true;
        var bo_break = false;
        var first_y = y2;
        var prev_x = value_x;
        for (i = 0; i < i_graph_width_half; i++)
            if (i < grapharray.length) {
                var value_y = y2 - Math.floor((grapharray[i] - r_minval) / val_range * H);
                if (bo_first) {
                    ctx.fillStyle = graphcolor;
                    ctx.fillRect(value_x, value_y, 1, 1);
                    bo_first = false;
                    first_y = value_y;
                    ctx.strokeStyle = graphcolor;
                    ctx.lineWidth = thick;
                    ctx.beginPath();
                    ctx.moveTo(value_x, value_y);
                } else
                    ctx.lineTo(value_x, value_y);
                prev_x = value_x;
                if (bo_break)
                    break;
                value_x -= (step + 1);
                if (value_x < x1)
                    bo_break = true;
            }
        if (!bo_first) {
            ctx.stroke();
            if (gtype_ag) {
                ctx.save();
                if (value_x < x1)
                    ctx.lineTo(x1, y2 + 1);
                else
                    ctx.lineTo(prev_x, y2 + 1);
                ctx.lineTo(x2 + 1, y2 + 1);
                ctx.lineTo(x2 + 1, first_y);
                ctx.clip();
                ctx.fillStyle = graphcolor;
                ctx.globalCompositeOperation = "lighter";
                ctx.globalAlpha = 0.33;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.restore();
            }
        }
    }
    if (showscale) {
        ctx.fillStyle = fontcolor;
        ctx.font = fontstyle + " " + fontvariant + " " + fontweight + " " + fontsize + " " + fontfamily;
        if (rightalign) {
            ctx.textBaseline = "alphabetic";
            ctx.fillText(r_minval, x2 - ctx.measureText(r_minval).width, y2);
            ctx.textBaseline = "hanging";
            ctx.fillText(r_maxval, x2 - ctx.measureText(r_maxval).width, y1 + 1);
        } else {
            ctx.textBaseline = "alphabetic";
            ctx.fillText(r_minval, x1 + 1, y2);
            ctx.textBaseline = "hanging";
            ctx.fillText(r_maxval, x1 + 1, y1 + 1);
        }
    }
    if (showvalue && !rightalign) {
        ctx.fillStyle = fontcolor;
        ctx.font = fontstyle + " " + fontvariant + " " + fontweight + " " + fontsize + " " + fontfamily;
        ctx.textBaseline = "hanging";
        ctx.fillText(grapharray[0], x2 - ctx.measureText(grapharray[0]).width, y1 + 1);
    }
    if (showframe) {
        ctx.fillStyle = framecolor;
        ctx.fillRect(0, 0, 1, canvas.height);
        ctx.fillRect(0, canvas.height - 1, canvas.width, 1);
        ctx.fillRect(canvas.width - 1, 0, 1, canvas.height - 1);
        ctx.fillRect(0, 0, canvas.width, 1);
    }
};

module.exports = { ClearGraph, DrawGraphDefault };
