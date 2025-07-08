import React from 'react';
import { useNavigate } from "react-router-dom"

const JobMatches = ({ matches, loading, error }) => {
  const navigate = useNavigate()

  const formatTimestamp = (timestamp) => {
    if (!timestamp || timestamp === "N/A") return "N/A"
    return new Date(timestamp * 1000).toLocaleDateString()
  }

  const formatPostedAt = (date) => {
    if (!date || date === "N/A") return "N/A"
    return new Date(date).toLocaleDateString()
  }

  const handleCardClick = (jobId) => {
    navigate(`/job-detail/${jobId || "unknown"}`)
  }

  const getMatchColor = (score) => {
    if (score >= 80) return "text-green-600 bg-green-100"
    if (score >= 70) return "text-blue-600 bg-blue-100"
    if (score >= 60) return "text-yellow-600 bg-yellow-100"
    return "text-gray-600 bg-gray-100"
  }

  const getMatchLabel = (score) => {
    if (score >= 80) return "Excellent Match"
    if (score >= 70) return "Great Match"
    if (score >= 60) return "Good Match"
    return "Fair Match"
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, index) => (
          <div key={index} className="animate-pulse">
            <div className="bg-gray-200 rounded-lg p-6 space-y-3">
              <div className="h-4 bg-gray-300 rounded w-3/4"></div>
              <div className="h-3 bg-gray-300 rounded w-1/2"></div>
              <div className="h-3 bg-gray-300 rounded w-full"></div>
              <div className="h-3 bg-gray-300 rounded w-2/3"></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (error && matches.length === 0) {
    return (
      <div className="text-center py-12">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">Error loading jobs</h3>
        <p className="mt-1 text-sm text-gray-500">There was a problem fetching your job matches.</p>
      </div>
    )
  }

  if (matches.length === 0) {
    return (
      <div className="text-center py-12">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No job matches found</h3>
        <p className="mt-1 text-sm text-gray-500">
          Upload your resume to discover personalized job opportunities that match your skills and experience.
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {matches.map((job, index) => (
        <div
          key={index}
          className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg hover:border-blue-300 transition-all duration-200 cursor-pointer group"
          onClick={() => handleCardClick(job.job_id)}
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors duration-200 line-clamp-2">
                {job.job_title || "Job Title Not Available"}
              </h3>
              {/* <p className="text-sm text-gray-600 mt-1">{job.company_name || "Company Name Not Available"}</p> */}
            </div>
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${getMatchColor(job.similarity_score*100 || 0)}`}>
              {(job.similarity_score*100 || 0).toFixed(0)}% Match
            </div>
          </div>

          {/* Location and Type */}
          <div className="flex items-center space-x-4 mb-3">
            <div className="flex items-center text-sm text-gray-500">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              {job.location || "Location Not Specified"}
              {job.is_remote && (
                <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">Remote</span>
              )}
            </div>
          </div>

          {/* Employment Type and Salary */}
          <div className="flex items-center justify-between mb-4">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {job.employment_type || "Not Specified"}
            </span>
            {job.salary_range && <span className="text-sm font-medium text-gray-900">{job.salary_range}</span>}
          </div>

          {/* Description */}
          <p className="text-sm text-gray-600 line-clamp-3 mb-4">
            {job.description || "No description available for this position."}
          </p>

          {/* Footer */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-100">
            <div className="flex items-center space-x-4 text-xs text-gray-500">
              <span>Posted: {formatPostedAt(job.posted_at)}</span>
              <span>•</span>
              <span>Matched: {formatTimestamp(job.posted_timestamp)}</span>
            </div>
            <div className="flex items-center text-blue-600 text-sm font-medium group-hover:text-blue-700">
              View Details
              <svg
                className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform duration-200"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>

          {/* Match Quality Indicator */}
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Match Quality</span>
              <span className={`text-xs font-medium ${getMatchColor(job.similarity_score*100 || 0).split(" ")[0]}`}>
                {getMatchLabel(job.similarity_score*100 || 0)}
              </span>
            </div>
            <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5">
              <div
                className={`h-1.5 rounded-full ${
                  getMatchColor(job.similarity_score*100 || 0).includes("green")
                    ? "bg-green-500"
                    : getMatchColor(job.similarity_score*100 || 0).includes("blue")
                      ? "bg-blue-500"
                      : getMatchColor(job.similarity_score*100 || 0).includes("yellow")
                        ? "bg-yellow-500"
                        : "bg-gray-500"
                }`}
                style={{ width: `${job.similarity_score*100 || 0}%` }}
              ></div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default JobMatches
