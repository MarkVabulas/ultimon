
var DrawArcGaugeDefault = function (dst, thickness, startangle, perc, bgcolor, color, fill, fillcolor, showtext, text, fontfamily, fontcolor, fontsize, fontstyle, fontvariant, fontweight) {
    var canvas = document.getElementById(dst);
    var ctx = canvas.getContext("2d");
    var W = canvas.width;
    var H = canvas.height;
    var startradians = startangle * Math.PI / 180;
    var endradians = (startangle + 360 * perc / 100) * Math.PI / 180;
    ctx.clearRect(0, 0, W, H);
    if (text == "")
        return;
    if (fill) {
        ctx.beginPath();
        ctx.strokeStyle = fillcolor;
        ctx.lineWidth = thickness / 2;
        ctx.arc(W / 2, H / 2, (W - thickness * 1.5) / 2, 0, Math.PI * 2, false);
        ctx.fillStyle = fillcolor;
        ctx.fill();
        ctx.stroke();
    }
    ctx.beginPath();
    ctx.strokeStyle = bgcolor;
    ctx.lineWidth = thickness;
    if (perc == 0)
        ctx.arc(W / 2, H / 2, (W - thickness) / 2, 0, Math.PI * 2, false);
    else
        ctx.arc(W / 2, H / 2, (W - thickness) / 2, endradians - Math.PI / 2, startradians - Math.PI / 2, false);
    ctx.stroke();
    if (perc > 0) {
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = thickness;
        ctx.arc(W / 2, H / 2, (W - thickness) / 2, startradians - Math.PI / 2, endradians - Math.PI / 2, false);
        ctx.stroke();
    }
    if (showtext) {
        ctx.fillStyle = fontcolor;
        ctx.font = fontstyle + " " + fontvariant + " " + fontweight + " " + fontsize + " " + fontfamily;
        ctx.textBaseline = "middle";
        ctx.fillText(text, W / 2 - ctx.measureText(text).width / 2, H / 2);
    }
};

module.exports = {
    DrawArcGaugeDefault
};
