import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Newspaper, Brain, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { triggerScraping, triggerLLMAnalysis, generatePartyReport } from '../utils/api';
import type { LLMAnalysisRequest } from '../utils/api';

const ScrapingAnalysisPage = () => {
  const navigate = useNavigate();

  // Scraping state
  const [scrapingLoading, setScrapingLoading] = useState(false);
  const [scrapingResult, setScrapingResult] = useState<any>(null);
  const [scrapingError, setScrapingError] = useState('');
  const [startDate, setStartDate] = useState('2024-10-01');
  const [endDate, setEndDate] = useState('2024-10-14');

  // Analysis state
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [analysisError, setAnalysisError] = useState('');
  const [analysisParty, setAnalysisParty] = useState('');
  const [analysisFigure, setAnalysisFigure] = useState('');
  const [analysisLimit, setAnalysisLimit] = useState(10);

  // Report state
  const [reportLoading, setReportLoading] = useState(false);
  const [reportResult, setReportResult] = useState<any>(null);
  const [reportError, setReportError] = useState('');
  const [reportParty, setReportParty] = useState('bnp');

  // Handle scraping
  const handleScraping = async () => {
    setScrapingLoading(true);
    setScrapingError('');
    setScrapingResult(null);

    try {
      const result = await triggerScraping(startDate, endDate);
      setScrapingResult(result);
    } catch (err: any) {
      setScrapingError(err.message || 'Failed to scrape newspapers');
    } finally {
      setScrapingLoading(false);
    }
  };

  // Handle LLM analysis
  const handleAnalysis = async () => {
    setAnalysisLoading(true);
    setAnalysisError('');
    setAnalysisResult(null);

    try {
      const request: LLMAnalysisRequest = {
        limit: analysisLimit,
        language: 'Bangla',
        include_summary: true,
        include_keywords: true,
        include_stance: true
      };

      if (analysisParty) request.party = analysisParty;
      if (analysisFigure) request.figure = analysisFigure;

      const result = await triggerLLMAnalysis(request);
      setAnalysisResult(result);
    } catch (err: any) {
      setAnalysisError(err.message || 'Failed to analyze articles');
    } finally {
      setAnalysisLoading(false);
    }
  };

  // Handle party report
  const handlePartyReport = async () => {
    setReportLoading(true);
    setReportError('');
    setReportResult(null);

    try {
      const result = await generatePartyReport(reportParty, 50, 'Bangla');
      setReportResult(result);
    } catch (err: any) {
      setReportError(err.message || 'Failed to generate party report');
    } finally {
      setReportLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Home
            </button>
            <h1 className="text-2xl font-bold text-gray-900">
              Scraping & Analysis
            </h1>
            <div className="w-24"></div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8 space-y-8">
        
        {/* Scraping Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center mb-6">
            <Newspaper className="w-6 h-6 text-blue-600 mr-3" />
            <h2 className="text-xl font-bold text-gray-900">Newspaper Scraping</h2>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Start Date
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  End Date
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <button
              onClick={handleScraping}
              disabled={scrapingLoading}
              className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
            >
              {scrapingLoading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Scraping...
                </>
              ) : (
                <>
                  <Newspaper className="w-5 h-5 mr-2" />
                  Start Scraping
                </>
              )}
            </button>

            {scrapingError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
                <AlertCircle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
                <p className="text-red-600">{scrapingError}</p>
              </div>
            )}

            {scrapingResult && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center mb-3">
                  <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                  <h3 className="font-semibold text-green-900">Scraping Completed!</h3>
                </div>
                <div className="space-y-2 text-sm text-gray-700">
                  <p><strong>Status:</strong> {scrapingResult.status}</p>
                  <p><strong>Articles Scraped:</strong> {scrapingResult.total_articles_scraped}</p>
                  <p><strong>Articles Stored:</strong> {scrapingResult.total_articles_stored}</p>
                  <p><strong>Processing Time:</strong> {scrapingResult.processing_time.toFixed(2)}s</p>
                  <p><strong>Message:</strong> {scrapingResult.message}</p>
                  {scrapingResult.articles_by_source && (
                    <div className="mt-3">
                      <p className="font-semibold mb-1">By Source:</p>
                      <ul className="list-disc list-inside pl-4">
                        {Object.entries(scrapingResult.articles_by_source).map(([source, count]) => (
                          <li key={source}>{source}: {count as number}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* LLM Analysis Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center mb-6">
            <Brain className="w-6 h-6 text-purple-600 mr-3" />
            <h2 className="text-xl font-bold text-gray-900">LLM Analysis</h2>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Party (Optional)
                </label>
                <input
                  type="text"
                  value={analysisParty}
                  onChange={(e) => setAnalysisParty(e.target.value)}
                  placeholder="e.g., BNP, NCP"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Figure (Optional)
                </label>
                <input
                  type="text"
                  value={analysisFigure}
                  onChange={(e) => setAnalysisFigure(e.target.value)}
                  placeholder="e.g., Tareq Rahman"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Limit
                </label>
                <input
                  type="number"
                  value={analysisLimit}
                  onChange={(e) => setAnalysisLimit(parseInt(e.target.value))}
                  min="1"
                  max="100"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>

            <button
              onClick={handleAnalysis}
              disabled={analysisLoading}
              className="w-full bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
            >
              {analysisLoading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Brain className="w-5 h-5 mr-2" />
                  Analyze Articles
                </>
              )}
            </button>

            {analysisError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
                <AlertCircle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
                <p className="text-red-600">{analysisError}</p>
              </div>
            )}

            {analysisResult && (
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center mb-3">
                  <CheckCircle className="w-5 h-5 text-purple-600 mr-2" />
                  <h3 className="font-semibold text-purple-900">Analysis Completed!</h3>
                </div>
                <div className="space-y-2 text-sm text-gray-700 mb-4">
                  <p><strong>Total Analyzed:</strong> {analysisResult.total_analyzed}</p>
                  <p><strong>Processing Time:</strong> {analysisResult.processing_time.toFixed(2)}s</p>
                </div>
                
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {analysisResult.analyses.map((analysis: any, idx: number) => (
                    <div key={idx} className="bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-2">{analysis.title}</h4>
                      {analysis.keywords && (
                        <div className="mb-2">
                          <p className="text-sm font-medium text-gray-700">Keywords:</p>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {analysis.keywords.keywords?.slice(0, 5).map((keyword: string, i: number) => (
                              <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                                {keyword}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {analysis.stance && (
                        <p className="text-sm text-gray-600">
                          <strong>Stance:</strong> {analysis.stance}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Party Report Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center mb-6">
            <Brain className="w-6 h-6 text-green-600 mr-3" />
            <h2 className="text-xl font-bold text-gray-900">Party Report</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Party
              </label>
              <select
                value={reportParty}
                onChange={(e) => setReportParty(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value="bnp">BNP</option>
                <option value="ji">Jamaat-e-Islami</option>
                <option value="ncp">National Citizens Party</option>
                <option value="ab_party">AB Party</option>
                <option value="gop">Gono Odhikar Parishad</option>
                <option value="gono_songhati">Gono Songhati</option>
                <option value="interim_government">Interim Government</option>
              </select>
            </div>

            <button
              onClick={handlePartyReport}
              disabled={reportLoading}
              className="w-full bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
            >
              {reportLoading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Brain className="w-5 h-5 mr-2" />
                  Generate Report
                </>
              )}
            </button>

            {reportError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
                <AlertCircle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
                <p className="text-red-600">{reportError}</p>
              </div>
            )}

            {reportResult && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center mb-3">
                  <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                  <h3 className="font-semibold text-green-900">Report Generated!</h3>
                </div>
                <div className="space-y-3 text-sm text-gray-700">
                  <p><strong>Party:</strong> {reportResult.party_name}</p>
                  <p><strong>Total Articles:</strong> {reportResult.total_articles}</p>
                  <p><strong>Articles Analyzed:</strong> {reportResult.articles_analyzed}</p>
                  
                  {reportResult.top_topics && Object.keys(reportResult.top_topics).length > 0 && (
                    <div>
                      <p className="font-semibold mb-1">Top Topics:</p>
                      <ul className="list-disc list-inside pl-4">
                        {Object.entries(reportResult.top_topics).slice(0, 5).map(([topic, count]) => (
                          <li key={topic}>{topic}: {count as number}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {reportResult.top_keywords && Object.keys(reportResult.top_keywords).length > 0 && (
                    <div>
                      <p className="font-semibold mb-1">Top Keywords:</p>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {Object.entries(reportResult.top_keywords).slice(0, 10).map(([keyword, count]) => (
                          <span key={keyword} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                            {keyword} ({count as number})
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

      </main>
    </div>
  );
};

export default ScrapingAnalysisPage;
