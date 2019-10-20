import {Component, ElementRef, EventEmitter, Input, OnChanges, OnInit, Output, ViewChild} from '@angular/core';
import * as d3 from 'd3';

@Component({
  selector: 'app-timeline-control',
  templateUrl: './timeline-control.component.html',
  styleUrls: ['./timeline-control.component.css']
})
export class TimelineControlComponent implements OnInit, OnChanges {
  @Input() domainMin: number;
  @Input() domainMax: number;
  @Input() title: string;
  @Input() unit: string;
  @Output() valueChanged = new EventEmitter<number>();
  canvasWidth: any = "100%";
  canvasHeight: any = "60px";
  @ViewChild('canvas')
  private canvasContainer: ElementRef;
  svg: any = null;
  rangePadding: number = 20;
  xScale: any = null;
  xOffset: number = 20;
  yOffset: number = 20;
  titleElement: any = null;
  fromTimeKnob: any = null;
  knobRadius: number = 8;

  constructor() { }

  ngOnInit() {
  }


  private createChart(): void {
    let domainMin = this.domainMin;
    let domainMax = this.domainMax;
    this.svg = d3.select("#canvas")
      .append("svg")
      .attr("width", this.canvasWidth)
      .attr("height", this.canvasHeight);

    let rangeMin = 0;
    let rangeMax = this.canvasContainer.nativeElement.offsetWidth -  2 * this.rangePadding;

    // xScale
    this.xScale = d3.scaleLinear()
      .domain([domainMin, domainMax])
      .range([rangeMin, rangeMax]);


    // Draw the axis
    this.svg
      .append("g")
      .attr("transform", "translate(" + this.xOffset + ", " + this.yOffset + ")")      // This controls the rotate position of the Axis
      .call(d3.axisBottom(this.xScale))
      .selectAll("text")
        .attr("transform", "translate(-10, 10)rotate(-45)")
        .style("text-anchor", "end")
        .style("font-size", 12)
        .style("fill", "#69a3b2");

    this.titleElement = this.svg.append("text");
    //

    this.fromTimeKnob = this.svg
      .append("circle")
      .attr("cx", this.xOffset)
      .attr("cy", this.yOffset)
      .attr("r", this.knobRadius)
      .call(d3.drag()
          .on("start", dragstarted.bind(this))
          .on("drag", dragged.bind(this))
          .on("end", dragended.bind(this)));

    function dragstarted() {
      d3.select(this).raise();
      this.fromTimeKnob.attr("cursor", "grabbing");
    }

    function dragged(d, i, n) {
      let thisX = d3.event.x;
      let newX = Math.min(Math.max(rangeMin + this.xOffset, thisX), rangeMax + this.xOffset);
      d3.select(n[i])
        .attr("cx", n[i].x = newX)
        .attr("cy", n[i].y = this.yOffset);
      let invertedX = this.xScale.invert(newX - this.xOffset);
      this.setTitleText(invertedX);

    }

    function dragended() {
      this.fromTimeKnob.attr("cursor", "grab");
      let invertedX = this.xScale.invert(d3.event.x);
      this.valueChanged.emit(invertedX);

    }

  }

  setTitleText(xValue) {
    let chartWidth = this.canvasContainer.nativeElement.offsetWidth;
    this.titleElement.text(`${this.title}: ${xValue} ${this.unit}`);
    let node = this.titleElement.node();
    let titleWidth = node.getBoundingClientRect().width;
    let newXValue = (this.canvasContainer.nativeElement.offsetWidth - titleWidth)/2;
    this.titleElement.attr("transform", "translate(" + newXValue + ", " + this.yOffset/2 + ")");

  }

  ngOnChanges() {
    d3.select("svg").remove();
    this.createChart();
    this.setTitleText(0);

  }

}
