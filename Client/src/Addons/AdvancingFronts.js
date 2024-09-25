class Program {
	gl;
	program;
	uniforms;

	constructor (gl, vertexShader, fragmentShader) {
		this.gl = gl;
		this.program = this.createProgram(vertexShader, fragmentShader);
		this.uniforms = this.getUniforms(this.program);
	}

	bind () {
		this.gl.useProgram(this.program);
	}

	createProgram (vertexShader, fragmentShader) {
		let program = this.gl.createProgram();
		this.gl.attachShader(program, vertexShader);
		this.gl.attachShader(program, fragmentShader);
		this.gl.linkProgram(program);
	
		if (!this.gl.getProgramParameter(program, gl.LINK_STATUS))
			console.trace(this.gl.getProgramInfoLog(program));
	
		return program;
	}

	getUniforms (program) {
		let uniforms = [];
		let uniformCount = this.gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS);
		for (let i = 0; i < uniformCount; i++) {
			let uniformName = this.gl.getActiveUniform(program, i).name;
			uniforms[uniformName] = this.gl.getUniformLocation(program, uniformName);
		}
		return uniforms;
	}
}

var canvas;
var gl, ext;
var document_width, document_height;
var viewport_width, viewport_height;
var pixelSize;

class AdvancingFronts {
	total_frame_count = 0;
	goal_fps = 30;
	fps = 30; // no hurdle for DX10 graphics cards
	delay = 1000 / this.goal_fps;
	it = 1;
	lightCoords = [0.5, 0.5];
	checkpoint = new Date().getTime();

	constructor() {
		this.load();
	}

	load()
	{
		canvas = document.getElementById('background');
		({ gl, ext } = AdvancingFronts.createWebGLContext(canvas));
		document_width = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
		document_height = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
		canvas.width = document_width;
		canvas.height = document_height;
		
		viewport_width = canvas.width;
		viewport_height = canvas.height;
		pixelSize = [1.0 / viewport_width, 1.0 / viewport_height];

		this.compileShaders();
	
		let posBuffer = gl.createBuffer();
		gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
		gl.enableVertexAttribArray(0);
	
		let vertices = new Float32Array([ -1, -1, 0, 1, -1, 0, -1, 1, 0, 1, 1, 0 ]);

		gl.bufferData(gl.ARRAY_BUFFER, vertices.byteLength, gl.STATIC_DRAW);
		gl.bufferSubData(gl.ARRAY_BUFFER, 0, vertices);
		gl.vertexAttribPointer(0, 3, gl.FLOAT, gl.FALSE, 0, 0);
	
		let noisepixels = [];
		let pixels = [];
		for ( let i = 0; i < viewport_width; i++) {
			for ( let j = 0; j < viewport_height; j++) {
				noisepixels.push(Math.random() * 255, Math.random() * 255, Math.random() * 255, 255);
				pixels.push(0, 0, 0, 255);
			}
		}
	
		{
			let rawDataNoise = new Uint8Array(noisepixels);
			this.texture_main_l = AdvancingFronts.createNewTexture(gl, rawDataNoise, gl.LINEAR);
			this.texture_main_n = AdvancingFronts.createNewTexture(gl, rawDataNoise, gl.NEAREST);
			this.texture_main2_l = AdvancingFronts.createNewTexture(gl, rawDataNoise, gl.LINEAR);
			this.texture_main2_n = AdvancingFronts.createNewTexture(gl, rawDataNoise, gl.NEAREST);
			this.texture_noise_l = AdvancingFronts.createNewTexture(gl, rawDataNoise, gl.LINEAR);
			this.texture_noise_n = AdvancingFronts.createNewTexture(gl, rawDataNoise, gl.NEAREST);
		}
	
		{
			let rawData = new Uint8Array(pixels);
			this.texture_helper = AdvancingFronts.createNewTexture(gl, rawData, gl.LINEAR);
			this.texture_blur = AdvancingFronts.createNewTexture(gl, rawData, gl.LINEAR);
		}
	
		this.FBO_main = AdvancingFronts.createNewFramebuffer(gl, this.texture_main_l);
		this.FBO_main2 = AdvancingFronts.createNewFramebuffer(gl, this.texture_main2_l);
		this.FBO_helper = AdvancingFronts.createNewFramebuffer(gl, this.texture_helper);
		this.FBO_blur = AdvancingFronts.createNewFramebuffer(gl, this.texture_blur);
		this.FBO_noise = AdvancingFronts.createNewFramebuffer(gl, this.texture_noise_l);
	
		this.prog_advance.bind();
		this.setUniforms(this.prog_advance);
	
		this.prog_blur_horizontal.bind();
		gl.uniform2f(this.prog_blur_horizontal.uniforms.pixelSize, pixelSize[0], pixelSize[1]);
		gl.uniform1i(this.prog_blur_horizontal.uniforms.src_tex, 0);
	
		this.prog_blur_vertical.bind();
		gl.uniform2f(this.prog_blur_vertical.uniforms.pixelSize, pixelSize[0], pixelSize[1]);
		gl.uniform1i(this.prog_blur_vertical.uniforms.src_tex, 0);
	
		this.prog_composite.bind();
		this.setUniforms(this.prog_composite);
	
		gl.activeTexture(gl.TEXTURE2);
		gl.bindTexture(gl.TEXTURE_2D, this.texture_blur);
	
		gl.activeTexture(gl.TEXTURE3);
		gl.bindTexture(gl.TEXTURE_2D, this.texture_noise_l);
	
		gl.activeTexture(gl.TEXTURE4);
		gl.bindTexture(gl.TEXTURE_2D, this.texture_noise_n);
	
		this.calculateBlurTexture();
	}

	compileShaders() {
		this.baseVertexShader = AdvancingFronts.compileShader(gl, gl.VERTEX_SHADER, `
			attribute vec3 aPos;
		
			void main(void) {
				gl_Position = vec4(aPos, 1.);
			}
		`);
		
		this.blurHorizontalShader = AdvancingFronts.compileShader(gl, gl.FRAGMENT_SHADER, `
			precision highp float;
		
			// original shader from http://www.gamerendering.com/2008/10/11/gaussian-blur-filter-shader/
			// horizontal blur fragment shader
			uniform sampler2D src_tex;
			uniform vec2 pixelSize;
			
			void main(void) // fragment
			{
				vec2 pixel = gl_FragCoord.xy * pixelSize;
		
				float h = pixelSize.x;
				vec4 sum = vec4(0.0);
				sum += texture2D(src_tex, vec2(pixel.x - 4.0*h, pixel.y) ) * 0.05;
				sum += texture2D(src_tex, vec2(pixel.x - 3.0*h, pixel.y) ) * 0.09;
				sum += texture2D(src_tex, vec2(pixel.x - 2.0*h, pixel.y) ) * 0.12;
				sum += texture2D(src_tex, vec2(pixel.x - 1.0*h, pixel.y) ) * 0.15;
				sum += texture2D(src_tex, vec2(pixel.x + 0.0*h, pixel.y) ) * 0.16;
				sum += texture2D(src_tex, vec2(pixel.x + 1.0*h, pixel.y) ) * 0.15;
				sum += texture2D(src_tex, vec2(pixel.x + 2.0*h, pixel.y) ) * 0.12;
				sum += texture2D(src_tex, vec2(pixel.x + 3.0*h, pixel.y) ) * 0.09;
				sum += texture2D(src_tex, vec2(pixel.x + 4.0*h, pixel.y) ) * 0.05;
				gl_FragColor.xyz = sum.xyz/0.98; // normalize
				gl_FragColor.a = 1.;
			} 
		`);
		
		this.blurVerticalShader = AdvancingFronts.compileShader(gl, gl.FRAGMENT_SHADER, `
			precision highp float;
		
			// original shader from http://www.gamerendering.com/2008/10/11/gaussian-blur-filter-shader/
			// vertical blur fragment shader
			uniform sampler2D src_tex;
			uniform vec2 pixelSize;
		
			void main(void) // fragment
			{
				vec2 pixel = gl_FragCoord.xy * pixelSize;
		
				float v = pixelSize.y;
				vec4 sum = vec4(0.0);
				sum += texture2D(src_tex, vec2(pixel.x, - 4.0*v + pixel.y) ) * 0.05;
				sum += texture2D(src_tex, vec2(pixel.x, - 3.0*v + pixel.y) ) * 0.09;
				sum += texture2D(src_tex, vec2(pixel.x, - 2.0*v + pixel.y) ) * 0.12;
				sum += texture2D(src_tex, vec2(pixel.x, - 1.0*v + pixel.y) ) * 0.15;
				sum += texture2D(src_tex, vec2(pixel.x, + 0.0*v + pixel.y) ) * 0.16;
				sum += texture2D(src_tex, vec2(pixel.x, + 1.0*v + pixel.y) ) * 0.15;
				sum += texture2D(src_tex, vec2(pixel.x, + 2.0*v + pixel.y) ) * 0.12;
				sum += texture2D(src_tex, vec2(pixel.x, + 3.0*v + pixel.y) ) * 0.09;
				sum += texture2D(src_tex, vec2(pixel.x, + 4.0*v + pixel.y) ) * 0.05;
				gl_FragColor.xyz = sum.xyz/0.98;
				gl_FragColor.a = 1.;
			}
		`);
		
		this.advanceShader = AdvancingFronts.compileShader(gl, gl.FRAGMENT_SHADER, `
			precision highp float;
		
			uniform sampler2D sampler_prev;
			uniform sampler2D sampler_prev_n;
			uniform sampler2D sampler_blur;
			uniform sampler2D sampler_noise;
			uniform sampler2D sampler_noise_n;
		
			uniform vec2 pixelSize;
			uniform vec4 rnd;
			uniform vec2 lightCoords;
			uniform float time;
			uniform float fps;
		
			const float CellScaling = 6.0;
		
			void main(void) {
				vec2 pixel = gl_FragCoord.xy * pixelSize;
		
				// grabbing the blurred gradients
				vec2 d = pixelSize * CellScaling;
				vec4 dx = (texture2D(sampler_blur, pixel + vec2(1,0)*d) - texture2D(sampler_blur, pixel - vec2(1,0)*d))*0.5;
				vec4 dy = (texture2D(sampler_blur, pixel + vec2(0,1)*d) - texture2D(sampler_blur, pixel - vec2(0,1)*d))*0.5;
				
				vec2 zoom_in = pixel + vec2(dx.x, dy.x) * pixelSize * 8.; // adding the traveling wave front
				vec2 rand_noise = texture2D(sampler_noise, zoom_in + vec2(rnd.x, rnd.y)).xy;
				gl_FragColor.x = texture2D(sampler_prev, zoom_in).x + (rand_noise.x-0.5)*0.0025 - 0.002; // decay with error diffusion
				gl_FragColor.x -= (texture2D(sampler_blur, zoom_in + (rand_noise-0.5)*pixelSize).x -
								texture2D(sampler_prev, zoom_in + (rand_noise-0.5)*pixelSize)).x*0.047; // reaction-diffusion
		
				gl_FragColor.a = 1.;
			}
		`);
		
		this.compositeShader = AdvancingFronts.compileShader(gl, gl.FRAGMENT_SHADER, `
			precision highp float;
		
			uniform sampler2D sampler_prev;
			uniform sampler2D sampler_prev_n;
			uniform sampler2D sampler_blur;
			uniform sampler2D sampler_noise;
			uniform sampler2D sampler_noise_n;
		
			uniform vec2 pixelSize;
			uniform vec2 aspect;
			uniform vec4 rnd;
			uniform vec2 lightCoords;
			uniform float time;
		
			const float DisplacementStrength = 3.0;
		
			const vec4 Gold = vec4(0.5, 1.0, 1.0, 1.0);
			const vec4 LightBlue = vec4(0.7, 1.5, 2.0, 1.0);
			const vec4 Purple = vec4(0.8, 1.25, 1.5, 1.0);
		
			const vec4 BaseColor = Gold;
		
			const vec4 LightContribution = vec4(8.0, 6.0, 2.0, 1.0);
		
			const float GradientLength = 2.0;
		
			void main(void) {
				vec2 pixel = gl_FragCoord.xy * pixelSize;
		
				vec2 lightSize=vec2(0.75);
		
				// grabbing the gradients
				vec2 d = pixelSize;
				vec4 dx = (texture2D(sampler_blur, pixel + vec2(1,0)*d) - texture2D(sampler_blur, pixel - vec2(1,0)*d))*0.5;
				vec4 dy = (texture2D(sampler_blur, pixel + vec2(0,1)*d) - texture2D(sampler_blur, pixel - vec2(0,1)*d))*0.5;
		
				// adding the pixel gradients
				d = pixelSize * GradientLength;
				dx += texture2D(sampler_prev, pixel + vec2(1,0)*d) - texture2D(sampler_prev, pixel - vec2(1,0)*d);
				dy += texture2D(sampler_prev, pixel + vec2(0,1)*d) - texture2D(sampler_prev, pixel - vec2(0,1)*d);
		
				vec2 displacement = vec2(dx.x,dy.x) * lightSize * DisplacementStrength; // using only the red gradient as displacement vector
				float light = pow(max(1.0 - distance(0.5 + (pixel-0.5) * aspect * lightSize + displacement, 0.5 + (lightCoords-0.5) * aspect * lightSize), 0.0 ), 4.0);
		
				// recoloring the lit up red channel
				float red_source = texture2D(sampler_prev, pixel + vec2(dx.x,dy.x) * pixelSize * 8.0).x;
				vec4 offset = vec4(-0.5, -1.0, -1.0, 0.0);
				vec4 rd = BaseColor * red_source + offset;
				gl_FragColor = mix(rd, LightContribution, light * 0.75 * vec4(1.0 - red_source)); 
				
				//gl_FragColor = texture2D(sampler_prev, pixel); // bypass
				gl_FragColor.a = 1.;
			}
		`);

		this.prog_advance = new Program(gl, this.baseVertexShader, this.advanceShader);
		this.prog_composite = new Program(gl, this.baseVertexShader, this.compositeShader);
		this.prog_blur_horizontal = new Program(gl, this.baseVertexShader, this.blurHorizontalShader);
		this.prog_blur_vertical = new Program(gl, this.baseVertexShader, this.blurVerticalShader);
	}
	
	setUniforms(program) {
		gl.uniform2f(program.uniforms.pixelSize, pixelSize[0], pixelSize[1]);
		gl.uniform4f(program.uniforms.rnd, Math.random(), Math.random(), Math.random(), Math.random());
		gl.uniform1f(program.uniforms.fps, this.fps);
		gl.uniform1f(program.uniforms.time, this.checkpoint);
		gl.uniform2f(program.uniforms.aspect, Math.max(1, viewport_width / viewport_height), Math.max(1, viewport_height / viewport_width));
		gl.uniform2f(program.uniforms.lightCoords, this.lightCoords[0], this.lightCoords[1]);
		gl.uniform1i(program.uniforms.sampler_prev, 0);
		gl.uniform1i(program.uniforms.sampler_prev_n, 1);
		gl.uniform1i(program.uniforms.sampler_blur, 2);
		gl.uniform1i(program.uniforms.sampler_noise, 3);
		gl.uniform1i(program.uniforms.sampler_noise_n, 4);
	}

	calculateBlurTexture() {
		// horizontal
		gl.viewport(0, 0, viewport_width, viewport_height);
		this.prog_blur_horizontal.bind();
		gl.activeTexture(gl.TEXTURE0);
		if (this.it < 0) {
			gl.bindTexture(gl.TEXTURE_2D,  this.texture_main2_l);
			gl.bindFramebuffer(gl.FRAMEBUFFER,  this.FBO_helper);
		} else {
			gl.bindTexture(gl.TEXTURE_2D,  this.texture_main_l);
			gl.bindFramebuffer(gl.FRAMEBUFFER,  this.FBO_helper);
		}
		gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
		gl.flush();

		// vertical
		gl.viewport(0, 0, viewport_width, viewport_height);
		this.prog_blur_vertical.bind();
		gl.activeTexture(gl.TEXTURE0);
		gl.bindTexture(gl.TEXTURE_2D,  this.texture_helper);
		gl.bindFramebuffer(gl.FRAMEBUFFER,  this.FBO_blur);
		gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
		gl.flush();
	}

	advance() {
		gl.viewport(0, 0, viewport_width, viewport_height);
		this.prog_advance.bind();
		this.setUniforms(this.prog_advance);
		if (this.it > 0) {
			gl.activeTexture(gl.TEXTURE0);
			gl.bindTexture(gl.TEXTURE_2D,  this.texture_main_l); // interpolated input
			gl.activeTexture(gl.TEXTURE1);
			gl.bindTexture(gl.TEXTURE_2D,  this.texture_main_n); // "nearest" input
			gl.bindFramebuffer(gl.FRAMEBUFFER,  this.FBO_main2); // write to buffer
		} else {
			gl.activeTexture(gl.TEXTURE0);
			gl.bindTexture(gl.TEXTURE_2D,  this.texture_main2_l); // interpolated
			gl.activeTexture(gl.TEXTURE1);
			gl.bindTexture(gl.TEXTURE_2D,  this.texture_main2_n); // "nearest"
			gl.bindFramebuffer(gl.FRAMEBUFFER,  this.FBO_main); // write to buffer
		}
		gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
		gl.flush();

		this.calculateBlurTexture();
		this.it = - this.it;
	}

	composite() {
		gl.viewport(0, 0, viewport_width, viewport_height);
		this.prog_composite.bind();
		this.setUniforms(this.prog_composite);
		if (this.it < 0) {
			gl.activeTexture(gl.TEXTURE0);
			gl.bindTexture(gl.TEXTURE_2D,  this.texture_main_l);
			gl.activeTexture(gl.TEXTURE1);
			gl.bindTexture(gl.TEXTURE_2D,  this.texture_main_n);
		} else {
			gl.activeTexture(gl.TEXTURE0);
			gl.bindTexture(gl.TEXTURE_2D,  this.texture_main2_l);
			gl.activeTexture(gl.TEXTURE1);
			gl.bindTexture(gl.TEXTURE_2D,  this.texture_main2_n);
		}
		gl.bindFramebuffer(gl.FRAMEBUFFER, null);

		gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
		gl.flush();
	}

	render_frame() {
		this.advance();
		this.composite();

		this.total_frame_count++;
	}

	static createWebGLContext (canvas) {
		function supportRenderTextureFormat (gl, internalFormat, format, type) {
			let texture = gl.createTexture();
			gl.bindTexture(gl.TEXTURE_2D, texture);
			gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
			gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
			gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
			gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
			gl.texImage2D(gl.TEXTURE_2D, 0, internalFormat, 4, 4, 0, format, type, null);
		
			let fbo = gl.createFramebuffer();
			gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
			gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
		
			let status = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
			return status == gl.FRAMEBUFFER_COMPLETE;
		}
		
		function getSupportedFormat (gl, internalFormat, format, type)
		{
			if (!supportRenderTextureFormat(gl, internalFormat, format, type))
			{
				switch (internalFormat)
				{
					case gl.R16F:
						return getSupportedFormat(gl, gl.RG16F, gl.RG, type);
					case gl.RG16F:
						return getSupportedFormat(gl, gl.RGBA16F, gl.RGBA, type);
					default:
						return null;
				}
			}
		
			return {
				internalFormat,
				format
			}
		}
	
		const params = { alpha: true, depth: false, stencil: false, antialias: false, preserveDrawingBuffer: false };
	
		let gl = canvas.getContext('webgl2', params);
		const isWebGL2 = !!gl;
		if (!isWebGL2)
			gl = canvas.getContext('webgl', params) || canvas.getContext('experimental-webgl', params);
	
		let halfFloat;
		let supportLinearFiltering;
		if (isWebGL2) {
			gl.getExtension('EXT_color_buffer_float');
			supportLinearFiltering = gl.getExtension('OES_texture_float_linear');
		} else {
			halfFloat = gl.getExtension('OES_texture_half_float');
			supportLinearFiltering = gl.getExtension('OES_texture_half_float_linear');
		}
	
		gl.clearColor(0.0, 0.0, 0.0, 1.0);
	
		const halfFloatTexType = isWebGL2 ? gl.HALF_FLOAT : halfFloat.HALF_FLOAT_OES;
		let formatRGBA;
		let formatRG;
		let formatR;
	
		if (isWebGL2)
		{
			formatRGBA = getSupportedFormat(gl, gl.RGBA16F, gl.RGBA, halfFloatTexType);
			formatRG = getSupportedFormat(gl, gl.RG16F, gl.RG, halfFloatTexType);
			formatR = getSupportedFormat(gl, gl.R16F, gl.RED, halfFloatTexType);
		}
		else
		{
			formatRGBA = getSupportedFormat(gl, gl.RGBA, gl.RGBA, halfFloatTexType);
			formatRG = getSupportedFormat(gl, gl.RGBA, gl.RGBA, halfFloatTexType);
			formatR = getSupportedFormat(gl, gl.RGBA, gl.RGBA, halfFloatTexType);
		}
	
		return {
			gl,
			ext: {
				formatRGBA,
				formatRG,
				formatR,
				halfFloatTexType,
				supportLinearFiltering
			}
		};
	}
	
	static compileShader(gl, type, source) {
		const shader = gl.createShader(type);
		gl.shaderSource(shader, source);
		gl.compileShader(shader);
	
		if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS))
			console.log(gl.getShaderInfoLog(shader));
	
		return shader;
	}
	
	static createNewTexture(gl, rawData, filter) {
		let new_texture = gl.createTexture();
		
		gl.bindTexture(gl.TEXTURE_2D, new_texture);
		gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
		gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, viewport_width, viewport_height, 0, gl.RGBA, gl.UNSIGNED_BYTE, rawData);
		gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter);
		gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
	
		return new_texture;
	}
	
	static createNewFramebuffer(gl, color_attachment) {
		let new_buffer = gl.createFramebuffer();
	
		gl.bindFramebuffer(gl.FRAMEBUFFER, new_buffer);
		gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, color_attachment, 0);
	
		return new_buffer;
	}
}

$(() => {

	var fronts = new AdvancingFronts();
	
	addEventListener("resize", (event) => {
		fronts = new AdvancingFronts();
	});

	function anim() {
		let ti = new Date().getTime();
		fronts.fps = Math.round(1000 / ( ti -  fronts.checkpoint ));
		fronts.checkpoint =  ti;

		if ( fronts.fps <  fronts.goal_fps)
			fronts.delay--;
		else
		fronts.delay++;

		fronts.render_frame();

		setTimeout(() => {
			requestAnimationFrame( anim );
		},  fronts.delay);
	}

	anim();
});

export default {};
