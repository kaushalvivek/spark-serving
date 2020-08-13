/*
 * Copyright (c) 2016 Villu Ruusmann
 *
 * This file is part of JPMML-SparkML
 *
 * JPMML-SparkML is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * JPMML-SparkML is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with JPMML-SparkML.  If not, see <http://www.gnu.org/licenses/>.
 */
package org.jpmml.sparkml;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.zip.ZipFile;

import com.beust.jcommander.JCommander;
import com.beust.jcommander.Parameter;
import com.beust.jcommander.ParameterException;
import com.google.common.io.CharStreams;
import org.apache.spark.ml.PipelineModel;
import org.apache.spark.sql.types.DataType;
import org.apache.spark.sql.types.StructType;
import org.dmg.pmml.PMML;
import org.jpmml.model.metro.MetroJAXBUtil;
import org.jpmml.sparkml.model.HasPredictionModelOptions;
import org.jpmml.sparkml.model.HasRegressionTableOptions;
import org.jpmml.sparkml.model.HasTreeOptions;

public class Main {

	@Parameter (
		names = "--help",
		description = "Show the list of configuration options and exit",
		help = true
	)
	private boolean help = false;

	@Parameter (
		names = "--schema-input",
		description = "Schema JSON input file",
		required = true
	)
	private File schemaInput = null;

	@Parameter (
		names = "--pipeline-input",
		description = "Pipeline ML input ZIP file or directory",
		required = true
	)
	private File pipelineInput = null;

	@Parameter (
		names = "--pmml-output",
		description = "PMML output file",
		required = true
	)
	private File output = null;

	/**
	 * @see HasPredictionModelOptions#OPTION_KEEP_PREDICTIONCOL
	 */
	@Parameter (
		names = "--X-keep_predictionCol",
		arity = 1,
		hidden = true
	)
	private Boolean keepPredictionCol = Boolean.TRUE;

	/**
	 * @see HasTreeOptions#OPTION_COMPACT
	 */
	@Parameter (
		names = "--X-compact",
		arity = 1,
		hidden = true
	)
	private Boolean compact = Boolean.TRUE;

	/**
	 * @see HasRegressionTableOptions#OPTION_LOOKUP_THRESHOLD
	 */
	@Parameter (
		names = "--X-lookup_threshold",
		hidden = true
	)
	private Integer lookupThreshold = null;

	/**
	 * @see HasRegressionTableOptions#OPTION_REPRESENTATION
	 */
	@Parameter (
		names = "--X-representation",
		hidden = true
	)
	private String representation = null;


	static
	public void main(String... args) throws Exception {
		Main main = new Main();

		JCommander commander = new JCommander(main);
		commander.setProgramName(Main.class.getName());

		try {
			commander.parse(args);
		} catch(ParameterException pe){
			StringBuilder sb = new StringBuilder();

			sb.append(pe.toString());
			sb.append("\n");

			commander.usage(sb);

			System.err.println(sb.toString());

			System.exit(-1);
		}

		if(main.help){
			StringBuilder sb = new StringBuilder();

			commander.usage(sb);

			System.out.println(sb.toString());

			System.exit(0);
		}

		main.run();
	}

	private void run() throws Exception {
		StructType schema;

		try(InputStream is = new FileInputStream(this.schemaInput)){
			String json = CharStreams.toString(new InputStreamReader(is, "UTF-8"));

			schema = (StructType)DataType.fromJson(json);
		}

		File pipelineDir = this.pipelineInput;

		zipFile:
		{
			ZipFile zipFile;

			try {
				zipFile = new ZipFile(pipelineDir);
			} catch(IOException ioe){
				break zipFile;
			}

			try {
				pipelineDir = File.createTempFile("PipelineModel", "");
				if(!pipelineDir.delete()){
					throw new IOException();
				}

				pipelineDir.mkdirs();

				ZipUtil.uncompress(zipFile, pipelineDir);
			} finally {
				zipFile.close();
			}
		}

		PipelineModel pipelineModel = PipelineModel.load(pipelineDir.getAbsolutePath());

		Map<String, Object> options = new LinkedHashMap<>();
		options.put(HasPredictionModelOptions.OPTION_KEEP_PREDICTIONCOL, this.keepPredictionCol);
		options.put(HasTreeOptions.OPTION_COMPACT, this.compact);
		options.put(HasRegressionTableOptions.OPTION_LOOKUP_THRESHOLD, this.lookupThreshold);
		options.put(HasRegressionTableOptions.OPTION_REPRESENTATION, this.representation);

		PMML pmml = new PMMLBuilder(schema, pipelineModel)
			.putOptions(options)
			.build();

		try(OutputStream os = new FileOutputStream(this.output)){
			MetroJAXBUtil.marshalPMML(pmml, os);
		}
	}

	public File getSchemaInput(){
		return this.schemaInput;
	}

	public void setSchemaInput(File schemaInput){
		this.schemaInput = schemaInput;
	}

	public File getPipelineInput(){
		return this.pipelineInput;
	}

	public void setPipelineInput(File pipelineInput){
		this.pipelineInput = pipelineInput;
	}

	public File getOutput(){
		return this.output;
	}

	public void setOutput(File output){
		this.output = output;
	}
}