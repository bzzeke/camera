
import * as d3 from 'd3';

export default class Zone {
    constructor (camera) {
        this.color = ''
        this.camera = camera;
        this.scaleFactor = 2;
        this.hasPolygon = false;
        this.dragging = false;
        this.drawing = false;
        this.startPoint = null;
        this.svg = d3.select(".container_svg");
        this.points = [];
        this.g = null
        this.dragger = d3.drag()
            .on('drag', this.handleDrag)
            .on('end', function(){
                this.dragging = false;
            });

        this.svg.on('mouseup', (event) => {
            if(this.dragging || this.hasPolygon) return;
            this.drawing = true;
            var point = [d3.pointer(event)[0], d3.pointer(event)[1]];

            if (event.target.hasAttribute('is-handle')) {
                this.closePolygon();
                return;
            }

            this.drawLine(point);
        });

        this.svg.on('mousemove', (event) => {
            if (!this.drawing) {
                return;
            }
            var g = this.svg.select('g.drawPoly');
            g.select('line').remove();
            g.append('line')
                .attr('x1', this.startPoint[0])
                .attr('y1', this.startPoint[1])
                .attr('x2', d3.pointer(event)[0] + 2)
                .attr('y2', d3.pointer(event)[1])
                .attr('stroke', '#53DBF3')
                .attr('stroke-width', 1);
        });

        this.clearPoligon();
        if (this.camera.detection.zone.length > 0) {
            this.drawPoints(this.toScaledPoints(this.camera.detection.zone));
        }
    }

    closePolygon() {
        this.svg.select('g.drawPoly').remove();
        var g = this.svg.append('g');
        g.append('polygon')
            .attr('points', this.points)
            .style('fill', this.color)
            .style('fill-opacity', 0.4);
        for(var i = 0; i < this.points.length; i++) {
            g.selectAll('circles')
                .data([this.points[i]])
                .enter()
                .append('circle')
                .attr('cx', this.points[i][0])
                .attr('cy', this.points[i][1])
                .attr('r', 4)
                .attr('fill', '#FDBC07')
                .attr('stroke', '#000')
                .attr('is-handle', 'true')
                .style({cursor: 'move'});
        }

        this.dragger(g.selectAll('circle'));
        this.points.splice(0);
        this.drawing = false;
        this.hasPolygon = true;
    }

    handleDrag(event) {
        if (this.drawing) {
            return;
        }

        var newPoints = [];
        this.dragging = true;

        d3.select(this).attr('cx', event.x).attr('cy', event.y);
        d3.select(this.parentNode).selectAll('circle').each(function() {
            var item = d3.select(this);
            newPoints.push([item.attr('cx'), item.attr('cy')]);
        });

        d3.select(this.parentNode).select('polygon').attr('points', newPoints);
    }

    clearPoligon() {
        this.svg.select('g').remove();
        this.hasPolygon = false;
    }

    drawLine(point) {

        this.startPoint = point;
        if(this.svg.select('g.drawPoly').empty()) this.g = this.svg.append('g').attr('class', 'drawPoly');

        this.points.push(point);
        this.g.select('polyline').remove();
        this.g.append('polyline').attr('points', this.points)
            .style('fill', 'none')
            .attr('stroke', '#000');
        for(var i = 0; i < this.points.length; i++) {
            this.g.append('circle')
                .attr('cx', this.points[i][0])
                .attr('cy', this.points[i][1])
                .attr('r', 4)
                .attr('fill', 'yellow')
                .attr('stroke', '#000')
                .attr('is-handle', 'true')
                .style({cursor: 'pointer'});
        }
    }

    getPoints() {
        if (this.hasPolygon) {
            return this.svg.select("g polygon").attr("points").split(",").map(p => parseInt(p));
        }

        return [];
    }

    toAbsolutePoints(points) {
        return points.map(p => p * this.scaleFactor);
    }

    toScaledPoints(points) {
        return points.map(p => parseInt(p / this.scaleFactor));
    }

    drawPoints(points) {
        while (points.length > 0) {
            let x = points.shift();
            let y = points.shift();

            this.drawLine([x, y]);
        }

        this.closePolygon();
    }

    get() {
        if (this.drawing == true) {
            return false;
        }

        return this.toAbsolutePoints(this.getPoints());
    }
}